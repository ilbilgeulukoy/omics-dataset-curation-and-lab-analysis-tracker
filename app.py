import streamlit as st
import pandas as pd
import plotly.express as px

from src.schema import REQUIRED_COLUMNS, RECOMMENDED_COLUMNS, ASSAY_SPECIFIC_COLUMNS, VALID_ASSAY_TYPES
from src.validation import validate_dataset_schema, add_path_availability_flags
from src.combination import generate_dataset_combinations

st.set_page_config(
    page_title="Omics Dataset Curation & Lab Analysis Tracker",
    page_icon="🧬",
    layout="wide"
)

st.title("🧬 Omics Dataset Curation & Lab Analysis Tracker")
st.subheader("Dataset curation, QC tracking and integration planning dashboard")

@st.cache_data
def load_dataset_summary():
    return pd.read_csv("data/mock_datasets.csv")

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

tab_dashboard, tab_schema, tab_templates = st.tabs([
    "📊 Dashboard",
    "📄 CSV Format Guide",
    "🧩 CSV Templates"
])

with tab_dashboard:
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

    st.header("📋 Dataset Summary Table")
    st.dataframe(filtered_df, use_container_width=True)

    st.caption(f"Showing {len(filtered_df)} of {len(df)} datasets after filters.")

    st.info("Metrics are calculated after applying the filters in the sidebar.")

    st.divider()

    st.header("🧬 Assay Type Summary")

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

    st.header("📊 Dataset Overview")

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

    st.header("🧪 Integration Planning Table")

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
    st.header("📄 CSV Format Guide")

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
    st.header("🧩 CSV Templates")

    st.write(
        """
        Use the CSV templates in the `templates/` folder to prepare your own data.
        Fill them manually in Excel, Numbers, LibreOffice or any text editor,
        then save the completed files into the `data/` folder.
        """
    )

    st.code(
        """
templates/datasets_template.csv
templates/sample_metadata_template.csv
templates/qc_summary_template.csv
        """,
        language="text"
    )

    st.subheader("Suggested workflow")

    st.code(
        """
cp templates/datasets_template.csv data/datasets.csv
cp templates/sample_metadata_template.csv data/sample_metadata.csv
cp templates/qc_summary_template.csv data/qc_summary.csv
        """,
        language="bash"
    )

    st.info(
        "In future versions, the app will read user-provided `data/datasets.csv` "
        "instead of the mock dataset file."
    )
