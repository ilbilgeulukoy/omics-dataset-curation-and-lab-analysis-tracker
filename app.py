import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
from pathlib import Path

from src.schema import REQUIRED_COLUMNS, RECOMMENDED_COLUMNS, ASSAY_SPECIFIC_COLUMNS, VALID_ASSAY_TYPES
from src.validation import validate_dataset_schema, add_path_availability_flags
from src.combination import generate_dataset_combinations
from src.knowledge_status import get_knowledge_status
from src.knowledge_graph import generate_knowledge_graph_html
from src.obsidian_notes import list_dataset_notes, read_dataset_note, get_note_path, list_protocol_notes, read_protocol_note
from src.obsidian_search import search_obsidian_notes
from src.rag_engine import answer_curation_question, count_indexed_chunks
from src.ui_components import inject_liquid_glass_theme, app_hero, glass_header, info_card

st.set_page_config(
    page_title="Omics Dataset Curation & Lab Analysis Tracker",
    page_icon="🧬",
    layout="wide"
)

inject_liquid_glass_theme()
app_hero()





@st.cache_data
def load_dataset_summary():
    user_dataset_path = Path("data/datasets.csv")
    mock_dataset_path = Path("data/mock_datasets.csv")

    if user_dataset_path.exists():
        return pd.read_csv(user_dataset_path)

    return pd.read_csv(mock_dataset_path)

df = load_dataset_summary()

# Convert numeric columns safely.
numeric_cols = [
    "n_patients",
    "n_samples",
    "n_cells_or_spots",
    "n_cells",
    "n_genes",
]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# Convert yes/no columns to booleans if they exist.
for col in ["verified", "include_for_analysis"]:
    if col in df.columns:
        df[col] = df[col].map({"yes": True, "no": False, True: True, False: False})

schema_result = validate_dataset_schema(df)
df = add_path_availability_flags(df)

tab_dashboard, tab_schema, tab_templates, tab_graph, tab_notes, tab_rag = st.tabs([
    "Dashboard",
    "CSV Format Guide",
    "CSV Templates",
    "Knowledge Graph",
    "Obsidian Notes",
    "Curation Assistant"
])

with tab_dashboard:
    glass_header("dashboard", "Dashboard", "Filter, inspect, and summarize curated omics datasets.")

    knowledge_status = get_knowledge_status()
    sqlite_counts = knowledge_status["sqlite_table_counts"]

    kb_col1, kb_col2, kb_col3, kb_col4 = st.columns(4)

    kb_col1.metric(
        "SQLite database",
        "Available" if knowledge_status["database_exists"] else "Missing"
    )

    kb_col2.metric(
        "Dataset table rows",
        sqlite_counts.get("datasets", 0)
    )

    kb_col3.metric(
        "H5AD manifest rows",
        sqlite_counts.get("h5ad_files", 0)
    )

    kb_col4.metric(
        "Obsidian notes",
        knowledge_status["obsidian_dataset_notes"]
    )

    with st.expander("Knowledge base paths"):
        st.write("SQLite database:")
        st.code(knowledge_status["database_path"])
        st.write("Obsidian vault:")
        st.code(knowledge_status["obsidian_vault_path"])

    st.caption(
        "SQLite stores structured dataset metadata, while Obsidian-compatible markdown notes store human-readable curation knowledge."
    )

    st.divider()

    if schema_result["is_valid"]:
        st.success("Dataset registry schema looks valid.")
    else:
        st.warning("Dataset registry schema needs attention.")

        if schema_result["missing_required_columns"]:
            st.error(
                "Missing required columns: "
                + ", ".join(schema_result["missing_required_columns"])
            )

        if schema_result["unknown_assay_types"]:
            st.error(
                "Unknown assay types: "
                + ", ".join(schema_result["unknown_assay_types"])
            )

    st.sidebar.header("Filters")

    if "assay_type" in df.columns:
        assay_filter = st.sidebar.multiselect(
            "Assay type",
            options=sorted(df["assay_type"].dropna().unique()),
            default=sorted(df["assay_type"].dropna().unique())
        )
    else:
        assay_filter = []

    verified_only = st.sidebar.checkbox("Only verified datasets", value=False)
    h5ad_only = st.sidebar.checkbox("Only datasets with H5AD", value=False)
    combination_only = st.sidebar.checkbox("Only include-for-analysis datasets", value=False)

    min_patients = st.sidebar.slider(
        "Minimum number of patients",
        min_value=0,
        max_value=int(df["n_patients"].max()) if "n_patients" in df.columns else 0,
        value=0
    )

    filtered_df = df.copy()

    if assay_filter and "assay_type" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["assay_type"].isin(assay_filter)]

    if verified_only and "verified" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["verified"] == True]

    if h5ad_only and "data_level" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["data_level"] == "h5ad"]

    if combination_only and "include_for_analysis" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["include_for_analysis"] == True]

    if "n_patients" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["n_patients"] >= min_patients]

    # Metrics are computed after filtering to avoid mixing scRNA-seq, spatial and bulk cohorts.
    total_datasets = len(filtered_df)
    total_patients = int(pd.to_numeric(filtered_df["n_patients"], errors="coerce").fillna(0).sum()) if "n_patients" in filtered_df.columns else 0

    if "n_cells_or_spots" in filtered_df.columns:
        total_cells = int(pd.to_numeric(filtered_df["n_cells_or_spots"], errors="coerce").fillna(0).sum())
    elif "n_cells" in filtered_df.columns:
        total_cells = int(pd.to_numeric(filtered_df["n_cells"], errors="coerce").fillna(0).sum())
    else:
        total_cells = 0

    h5ad_available = int((filtered_df["data_level"] == "h5ad").sum()) if "data_level" in filtered_df.columns else 0
    qc_reports = int(filtered_df["qc_report_path_provided"].sum()) if "qc_report_path_provided" in filtered_df.columns else 0

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Filtered datasets", total_datasets)
    col2.metric("Filtered patients", total_patients)
    col3.metric("Filtered cells/spots", f"{total_cells:,}")
    col4.metric("H5AD datasets", h5ad_available)
    col5.metric("QC reports", qc_reports)

    st.divider()

    st.header("Dataset Summary Table")

    technology_view = st.selectbox(
        "Technology view",
        [
            "All technologies",
            "scRNA-seq / single-cell",
            "Spatial / Visium",
            "bulk RNA-seq",
            "simulated transcriptomics",
        ],
        key="dataset_summary_technology_view",
    )

    def select_existing_columns(table, columns):
        return [column for column in columns if column in table.columns]

    if technology_view == "Spatial / Visium":
        spatial_report_path = "reports/spatial_readiness_summary.csv"
        spatial_demo_path = "data/mock_spatial_readiness.csv"

        try:
            spatial_df = pd.read_csv(spatial_report_path)
            spatial_source = spatial_report_path
        except FileNotFoundError:
            try:
                spatial_df = pd.read_csv(spatial_demo_path)
                spatial_source = spatial_demo_path
            except FileNotFoundError:
                spatial_df = pd.DataFrame()
                spatial_source = None

        if spatial_df.empty:
            st.warning("No spatial readiness file found. Expected: reports/spatial_readiness_summary.csv or data/mock_spatial_readiness.csv")
        else:
            st.caption(f"Spatial readiness source: {spatial_source}")
            spatial_columns = select_existing_columns(
                spatial_df,
                [
                    "dataset_id",
                    "sample_id",
                    "technology",
                    "assay_type",
                    "species",
                    "tissue",
                    "disease_context",
                    "matrix_files_found",
                    "spatial_folder_found",
                    "positions_found",
                    "scalefactors_found",
                    "image_found",
                    "metadata_found",
                    "n_spots",
                    "n_genes",
                    "readiness_status",
                    "clustering_suitability",
                    "include_for_analysis",
                    "notes",
                ],
            )
            st.dataframe(spatial_df[spatial_columns], use_container_width=True)
            st.caption(f"Showing {len(spatial_df)} spatial / Visium samples from the selected readiness source.")
            st.info("Spatial readiness focuses on matrix files, spatial coordinates, scalefactors, histology images, metadata, and analysis-readiness status.")

    else:
        summary_df = filtered_df.copy()

        if technology_view == "scRNA-seq / single-cell" and "assay_type" in summary_df.columns:
            summary_df = summary_df[
                summary_df["assay_type"].astype(str).str.contains("scrna|single", case=False, na=False)
            ]

        elif technology_view == "bulk RNA-seq" and "assay_type" in summary_df.columns:
            summary_df = summary_df[
                summary_df["assay_type"].astype(str).str.contains("bulk", case=False, na=False)
            ]

        elif technology_view == "simulated transcriptomics" and "assay_type" in summary_df.columns:
            summary_df = summary_df[
                summary_df["assay_type"].astype(str).str.contains("simulated", case=False, na=False)
            ]

        if technology_view == "All technologies":
            summary_columns = select_existing_columns(
                summary_df,
                [
                    "dataset_id",
                    "dataset_name",
                    "assay_type",
                    "species",
                    "disease_area",
                    "n_patients",
                    "n_samples",
                    "n_cells_or_spots",
                    "n_genes",
                    "data_level",
                    "verified",
                    "include_for_analysis",
                    "notes",
                ],
            )
        else:
            summary_columns = select_existing_columns(
                summary_df,
                [
                    "dataset_id",
                    "dataset_name",
                    "assay_type",
                    "species",
                    "disease_area",
                    "n_patients",
                    "n_samples",
                    "n_cells_or_spots",
                    "n_genes",
                    "data_level",
                    "data_access",
                    "verified",
                    "include_for_analysis",
                    "preprocessing_status",
                    "qc_report_path",
                    "notes",
                ],
            )

        st.dataframe(summary_df[summary_columns], use_container_width=True)
        st.caption(f"Showing {len(summary_df)} of {len(df)} datasets for this technology view.")
        st.info("Metrics are calculated after applying the filters in the sidebar.")

    st.divider()

    st.header("Assay Type Summary")

    if "assay_type" in filtered_df.columns:
        assay_summary = (
            filtered_df
            .groupby("assay_type", dropna=False)
            .agg(
                n_datasets=("dataset_id", "count"),
                total_patients=("n_patients", "sum"),
                total_samples=("n_samples", "sum"),
                total_cells_or_spots=("n_cells_or_spots", "sum"),
                mean_genes=("n_genes", "mean"),
            )
            .reset_index()
        )

        assay_summary["mean_genes"] = assay_summary["mean_genes"].round(0).astype(int)

        st.dataframe(assay_summary, use_container_width=True)

    st.divider()

    st.header("Dataset Overview")

    col_a, col_b = st.columns(2)

    with col_a:
        if "n_patients" in filtered_df.columns and "dataset_name" in filtered_df.columns:
            fig_patients = px.bar(
                filtered_df.sort_values("n_patients", ascending=False),
                x="dataset_name",
                y="n_patients",
                title="Number of patients per dataset"
            )
            st.plotly_chart(fig_patients, use_container_width=True)

    with col_b:
        cell_col = "n_cells" if "n_cells" in filtered_df.columns else "n_cells_or_spots" if "n_cells_or_spots" in filtered_df.columns else None
        if cell_col and "dataset_name" in filtered_df.columns:
            fig_cells = px.bar(
                filtered_df.sort_values(cell_col, ascending=False),
                x="dataset_name",
                y=cell_col,
                title="Number of cells/spots per dataset"
            )
            st.plotly_chart(fig_cells, use_container_width=True)

    if "n_patients" in filtered_df.columns and "n_genes" in filtered_df.columns:
        cell_col = "n_cells" if "n_cells" in filtered_df.columns else "n_cells_or_spots" if "n_cells_or_spots" in filtered_df.columns else None

        fig_genes = px.scatter(
            filtered_df,
            x="n_patients",
            y="n_genes",
            size=cell_col if cell_col else None,
            hover_name="dataset_name" if "dataset_name" in filtered_df.columns else None,
            title="Dataset size vs gene coverage"
        )

        st.plotly_chart(fig_genes, use_container_width=True)

    st.divider()

    st.header("Integration Planning Table")

    available_cols = [
        col for col in [
            "dataset_name",
            "assay_type",
            "n_patients",
            "n_cells",
            "n_cells_or_spots",
            "n_samples",
            "n_genes",
            "verified",
            "include_for_analysis",
            "notes"
        ]
        if col in filtered_df.columns
    ]

    integration_df = filtered_df[available_cols].copy()

    sort_cols = [col for col in ["include_for_analysis", "n_patients", "n_genes"] if col in integration_df.columns]
    if sort_cols:
        integration_df = integration_df.sort_values(
            by=sort_cols,
            ascending=[False] * len(sort_cols)
        )

    st.dataframe(integration_df, use_container_width=True)

    st.divider()

    st.header("Dataset Combination Optimizer")

    st.write(
        """
        This module ranks candidate scRNA-seq dataset combinations using preprocessing-passed h5ad sample files.
        It computes exact common gene intersections from adata.var_names and ranks combinations by total patients,
        common genes and total cells. No score or heuristic penalty is used.
        """
    )

    h5ad_path_file = st.text_input(
        "H5AD path list file",
        value="data/sample_h5ad_paths.csv",
        help="CSV file containing dataset_name, sample_id and h5ad_path columns."
    )

    opt_col1, opt_col2, opt_col3, opt_col4 = st.columns(4)

    with opt_col1:
        min_common_genes = st.number_input(
            "Minimum common genes",
            min_value=0,
            max_value=30000,
            value=18000,
            step=500,
        )

    with opt_col2:
        min_total_patients = st.number_input(
            "Minimum total patients",
            min_value=0,
            max_value=500,
            value=0,
            step=5,
        )

    with opt_col3:
        min_total_cells = st.number_input(
            "Minimum total cells",
            min_value=0,
            max_value=5000000,
            value=0,
            step=50000,
        )

    with opt_col4:
        max_datasets = st.number_input(
            "Maximum datasets in combination",
            min_value=2,
            max_value=30,
            value=10,
            step=1,
        )

    combination_df, h5ad_dataset_summary_df = generate_dataset_combinations(
        filtered_df,
        h5ad_path_file=h5ad_path_file,
        min_common_genes=int(min_common_genes),
        min_total_patients=int(min_total_patients),
        min_total_cells=int(min_total_cells),
        max_datasets=int(max_datasets),
    )

    st.subheader("H5AD-derived dataset summary")

    if h5ad_dataset_summary_df.empty:
        st.warning("The H5AD manifest was loaded, but no H5AD files were readable on this machine. Check that the paths in sample_h5ad_paths.csv exist locally, or run the app on the server where the files are stored.")
    else:
        st.dataframe(h5ad_dataset_summary_df, use_container_width=True)

    st.subheader("Combination results")

    if combination_df.empty:
        st.warning("No dataset combination matches the current criteria.")
    else:
        st.success(f"{len(combination_df)} valid combinations found.")

        st.dataframe(
            combination_df.head(100),
            use_container_width=True
        )

        csv = combination_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download combination results as CSV",
            data=csv,
            file_name="dataset_combination_results.csv",
            mime="text/csv",
        )

with tab_schema:
    glass_header("database", "CSV Format Guide", "Review required and recommended metadata fields.")
    st.header("CSV Format Guide")

    st.write(
        """
        The dashboard is designed around a universal dataset registry.
        Each row represents one omics dataset, study, cohort or experiment.
        """
    )

    st.subheader("Required columns")
    st.dataframe(pd.DataFrame({"required_column": REQUIRED_COLUMNS}), use_container_width=True)

    st.subheader("Recommended columns")
    st.dataframe(pd.DataFrame({"recommended_column": RECOMMENDED_COLUMNS}), use_container_width=True)

    st.subheader("Valid assay types")
    st.dataframe(pd.DataFrame({"assay_type": VALID_ASSAY_TYPES}), use_container_width=True)

    st.subheader("Assay-specific optional columns")

    for assay, columns in ASSAY_SPECIFIC_COLUMNS.items():
        with st.expander(assay):
            st.dataframe(pd.DataFrame({"optional_column": columns}), use_container_width=True)

with tab_templates:
    glass_header("template", "CSV Templates", "Download standardized input templates for the tracker.")
    st.header("CSV Templates")

    st.write(
        """
        Download the CSV templates, fill them manually in Excel, Numbers,
        LibreOffice or any spreadsheet editor, then save the completed files
        into the `data/` folder.
        """
    )

    template_files = {
        "Dataset registry template": "templates/datasets_template.csv",
        "Sample metadata template": "templates/sample_metadata_template.csv",
        "QC summary template": "templates/qc_summary_template.csv",
        "Sample H5AD paths template": "templates/sample_h5ad_paths_template.csv",
        "Visium registry template": "templates/visium_registry_template.csv",
    }

    for label, file_path in template_files.items():
        template_path = Path(file_path)

        if template_path.exists():
            st.download_button(
                label=f"Download {label}",
                data=template_path.read_text(),
                file_name=template_path.name,
                mime="text/csv",
            )
        else:
            st.warning(f"Template file not found: {file_path}")

    st.subheader("How to use the templates")

    st.write(
        """
        1. Download the templates above.
        2. Fill them with your own dataset information.
        3. Save the completed files as:
        """
    )

    st.code(
        """
data/datasets.csv
data/sample_metadata.csv
data/qc_summary.csv
data/sample_h5ad_paths.csv
data/visium_registry.csv
        """,
        language="text"
    )

    st.write(
        """
        For the exact H5AD-based combination optimizer, the most important file is:
        """
    )

    st.code("data/sample_h5ad_paths.csv", language="text")

    st.write(
        """
        For Spatial / Visium readiness validation, fill the Visium registry template,
        save it as `data/visium_registry.csv`, then run:
        """
    )

    st.code(
        "python scripts/validate_visium_dataset.py --registry-csv data/visium_registry.csv --output-csv reports/spatial_readiness_summary.csv",
        language="bash"
    )

    st.info(
        "The template files are small CSV files. Large H5AD, FASTQ, MTX or count matrix files should not be uploaded to GitHub."
    )



with tab_graph:
    glass_header("graph", "Dataset Knowledge Graph", "Explore relationships between datasets, papers, accessions, platforms, and curation states.")
    st.write("Interactive graph view for datasets, metadata, and optional H5AD/sample relationships.")

    graph_meta = generate_knowledge_graph_html()
    available_groups = graph_meta.get("available_groups", [])
    available_datasets = graph_meta.get("available_datasets", [])

    control_col, graph_col = st.columns([1, 3])

    with control_col:
        st.subheader("Graph controls")

        enabled_groups = st.multiselect(
            "Visible node groups",
            options=available_groups,
            default=[g for g in available_groups if g not in ["Sample", "H5AD file"]],
        )

        focus_dataset = st.selectbox(
            "Focus on one dataset",
            options=["All datasets"] + available_datasets,
            index=0,
        )

        include_h5ad = st.checkbox("Include sample/H5AD nodes", value=False)

        max_h5ad_per_dataset = st.slider(
            "Max H5AD/sample nodes per dataset",
            min_value=1,
            max_value=20,
            value=5,
        )

        gravity = st.slider(
            "Repel force",
            min_value=-200,
            max_value=-20,
            value=-90,
            step=5,
        )

        spring_length = st.slider(
            "Link distance",
            min_value=80,
            max_value=260,
            value=140,
            step=5,
        )

        central_gravity = st.slider(
            "Center force",
            min_value=0.0,
            max_value=0.1,
            value=0.02,
            step=0.005,
        )

        render_graph = st.button("Render graph")

        st.caption("Tip: turn off H5AD nodes first, then enable them after the main structure looks clean.")

    with graph_col:
        if render_graph or True:
            graph_status = generate_knowledge_graph_html(
                enabled_groups=enabled_groups,
                focus_dataset=None if focus_dataset == "All datasets" else focus_dataset,
                include_h5ad=include_h5ad,
                max_h5ad_per_dataset=max_h5ad_per_dataset,
                gravity=gravity,
                spring_length=spring_length,
                central_gravity=central_gravity,
            )

            if graph_status["success"] and graph_status["html_path"]:
                st.caption(
                    f"Nodes: {graph_status['n_nodes']} | Edges: {graph_status['n_edges']}"
                )

                html_path = Path(graph_status["html_path"])
                html_content = html_path.read_text(encoding="utf-8")

                components.html(
                    html_content,
                    height=860,
                    scrolling=True,
                )
            else:
                st.warning("Knowledge graph could not be generated.")


with tab_notes:
    glass_header("notes", "Obsidian Curation Notes", "Browse and search generated markdown notes.")

    st.write(
        "Browse the Obsidian-compatible markdown notes generated from the SQLite dataset registry."
    )

    st.divider()

    st.subheader("Search curation notes")

    search_query = st.text_input(
        "Search query",
        placeholder="Example: incomplete metadata, H5AD, preprocessing, synthetic disease area, 10x Genomics"
    )

    if search_query:
        search_results = search_obsidian_notes(search_query, max_results=12)

        if search_results:
            st.caption(f"Found {len(search_results)} matching note sections.")

            for result in search_results:
                with st.expander(
                    f"{result['file']} | {result['section']} | score {result['score']}"
                ):
                    st.write(result["preview"])
        else:
            st.info("No matching notes found.")

    dataset_notes = list_dataset_notes()
    protocol_notes = list_protocol_notes()

    note_col, preview_col = st.columns([1, 2])

    with note_col:
        st.subheader("Dataset notes")

        if dataset_notes:
            selected_note = st.selectbox(
                "Select dataset note",
                options=dataset_notes,
            )

            st.caption("Markdown file path:")
            st.code(get_note_path(selected_note))
        else:
            selected_note = None
            st.warning("No dataset notes found. Run scripts/export_datasets_to_obsidian.py first.")

        st.divider()

        st.subheader("Protocol notes")

        if protocol_notes:
            selected_protocol = st.selectbox(
                "Select protocol note",
                options=protocol_notes,
            )
        else:
            selected_protocol = None
            st.info("No protocol notes found.")

    with preview_col:
        if selected_note:
            st.subheader("Dataset note preview")
            note_content = read_dataset_note(selected_note)
            st.markdown(note_content)

        if selected_protocol:
            st.divider()
            st.subheader("Protocol note preview")
            protocol_content = read_protocol_note(selected_protocol)
            st.markdown(protocol_content)


with tab_rag:
    glass_header("assistant", "SQL-backed Curation Assistant", "Retrieve evidence from indexed Obsidian notes using SQLite full-text search.")

    info_card("""
<strong>How the curation assistant works</strong><br>
Obsidian markdown notes are split into sections, indexed into SQLite as note chunks,
and searched with SQLite full-text search. The assistant retrieves matching evidence
sections and displays grounded answers with source note paths. This is a lightweight
retrieval system for dataset curation decisions, not a biological interpretation model.
""")

    st.write(
        "Ask questions over the indexed Obsidian curation notes. Retrieval is powered by SQLite full-text search."
    )

    indexed_chunks = count_indexed_chunks()

    col_rag_1, col_rag_2 = st.columns(2)
    col_rag_1.metric("Indexed note chunks", indexed_chunks)
    col_rag_2.metric("Retrieval backend", "SQLite FTS")

    if indexed_chunks == 0:
        st.warning(
            "No indexed note chunks found. Run scripts/index_obsidian_notes_to_sqlite.py first."
        )

    example_queries = [
        "Which datasets mention metadata?",
        "Which datasets have H5AD information?",
        "What is the preprocessing status?",
        "Which notes mention synthetic disease area?",
        "Which datasets mention 10x Genomics?",
        "Which curation notes discuss data limitations?",
    ]

    selected_example = st.selectbox(
        "Example question",
        options=["Write my own question"] + example_queries,
    )

    default_query = "" if selected_example == "Write my own question" else selected_example

    rag_query = st.text_area(
        "Question",
        value=default_query,
        placeholder="Example: Which datasets have incomplete metadata or H5AD information?",
        height=100,
    )

    max_results = st.slider(
        "Number of retrieved sections",
        min_value=3,
        max_value=15,
        value=8,
    )

    if st.button("Ask curation assistant"):
        if not rag_query.strip():
            st.info("Write a question first.")
        else:
            rag_response = answer_curation_question(
                query=rag_query,
                max_results=max_results,
            )

            st.subheader("Answer")
            st.text(rag_response["answer"])

            st.subheader("Retrieved evidence")

            if rag_response["results"]:
                for result in rag_response["results"]:
                    with st.expander(
                        f"{result['note_name']} | {result['section_heading']} | {result['file_path']}"
                    ):
                        st.write(result["content"])
            else:
                st.info("No evidence retrieved.")

