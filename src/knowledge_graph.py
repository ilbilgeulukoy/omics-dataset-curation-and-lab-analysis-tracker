from pathlib import Path
import sqlite3
import pandas as pd
import networkx as nx
from pyvis.network import Network


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "omics_tracker.db"
REPORTS_DIR = PROJECT_ROOT / "reports"
GRAPH_HTML_PATH = REPORTS_DIR / "knowledge_graph.html"


GROUP_STYLES = {
    "Dataset": {"color": "#7FDBFF", "size": 34},
    "Accession": {"color": "#FFD166", "size": 16},
    "Assay type": {"color": "#B388FF", "size": 22},
    "Disease area": {"color": "#FF5D8F", "size": 22},
    "Species": {"color": "#50E3C2", "size": 16},
    "Platform": {"color": "#4FC3F7", "size": 16},
    "Paper": {"color": "#FF9E80", "size": 14},
    "Data level": {"color": "#C3F0CA", "size": 14},
    "Verification status": {"color": "#FFE082", "size": 14},
    "Preprocessing status": {"color": "#9CCC65", "size": 14},
    "Sample": {"color": "#F48FB1", "size": 10},
    "H5AD file": {"color": "#90CAF9", "size": 8},
}


def load_table(table_name: str) -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()

    with sqlite3.connect(DB_PATH) as connection:
        try:
            return pd.read_sql_query(f"SELECT * FROM {table_name}", connection)
        except Exception:
            return pd.DataFrame()


def load_datasets() -> pd.DataFrame:
    return load_table("datasets")


def load_h5ad_files() -> pd.DataFrame:
    return load_table("h5ad_files")


def safe_value(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def add_node(graph: nx.Graph, node_id: str, label: str, group: str, title: str = "") -> None:
    if not node_id or not label:
        return

    style = GROUP_STYLES.get(group, {"color": "#CCCCCC", "size": 12})

    graph.add_node(
        node_id,
        label=label,
        group=group,
        color=style["color"],
        size=style["size"],
        title=title or f"{group}: {label}",
        font={
            "color": "#EAEAEA",
            "size": 18 if group == "Dataset" else 12,
            "face": "Arial",
        },
        borderWidth=1.5,
    )


def add_edge(graph: nx.Graph, source: str, target: str, relation: str) -> None:
    graph.add_edge(
        source,
        target,
        title=relation,
        color={
            "color": "rgba(180, 220, 255, 0.20)",
            "highlight": "#7FDBFF",
        },
        width=1.0,
        smooth={"type": "continuous"},
    )


def build_graph(
    datasets_df: pd.DataFrame,
    h5ad_df: pd.DataFrame,
    enabled_groups=None,
    focus_dataset=None,
    include_h5ad=False,
    max_h5ad_per_dataset=5,
):
    if enabled_groups is None:
        enabled_groups = list(GROUP_STYLES.keys())

    graph = nx.Graph()

    for _, row in datasets_df.iterrows():
        dataset_id = safe_value(row.get("dataset_id", ""))
        dataset_name = safe_value(row.get("dataset_name", "")) or dataset_id

        if not dataset_id:
            continue

        if focus_dataset and dataset_id != focus_dataset and dataset_name != focus_dataset:
            continue

        accession = safe_value(row.get("accession", ""))
        assay_type = safe_value(row.get("assay_type", ""))
        disease_area = safe_value(row.get("disease_area", ""))
        species = safe_value(row.get("species", ""))
        platform = safe_value(row.get("platform", ""))
        paper_title = safe_value(row.get("paper_title", ""))
        data_level = safe_value(row.get("data_level", ""))
        verification_status = safe_value(row.get("data_verification_status", ""))
        preprocessing_status = safe_value(row.get("preprocessing_status", ""))
        n_patients = safe_value(row.get("n_patients", ""))
        n_samples = safe_value(row.get("n_samples", ""))
        n_cells_or_spots = safe_value(row.get("n_cells_or_spots", ""))

        dataset_node = f"dataset::{dataset_id}"

        dataset_title = f"""
        <b>{dataset_name}</b><br>
        Dataset ID: {dataset_id}<br>
        Accession: {accession}<br>
        Assay type: {assay_type}<br>
        Disease area: {disease_area}<br>
        Patients: {n_patients}<br>
        Samples: {n_samples}<br>
        Cells/spots: {n_cells_or_spots}
        """

        if "Dataset" in enabled_groups:
            add_node(graph, dataset_node, dataset_name, "Dataset", dataset_title)

        metadata_links = [
            ("accession", accession, "Accession", "has accession"),
            ("assay", assay_type, "Assay type", "has assay type"),
            ("disease", disease_area, "Disease area", "studies disease area"),
            ("species", species, "Species", "uses species"),
            ("platform", platform, "Platform", "uses platform"),
            ("paper", paper_title, "Paper", "described by paper"),
            ("data_level", data_level, "Data level", "has data level"),
            ("verification", verification_status, "Verification status", "has verification status"),
            ("preprocessing", preprocessing_status, "Preprocessing status", "has preprocessing status"),
        ]

        for prefix, value, group, relation in metadata_links:
            if not value or group not in enabled_groups or "Dataset" not in enabled_groups:
                continue

            node_id = f"{prefix}::{value}"
            label = value[:70] + "..." if len(value) > 70 else value
            add_node(graph, node_id, label, group, f"<b>{group}</b><br>{value}")
            add_edge(graph, dataset_node, node_id, relation)

        if include_h5ad and not h5ad_df.empty and "Sample" in enabled_groups and "H5AD file" in enabled_groups:
            subset = h5ad_df[h5ad_df["dataset_id"].astype(str) == dataset_id].head(max_h5ad_per_dataset)

            for _, hrow in subset.iterrows():
                sample_id = safe_value(hrow.get("sample_id", ""))
                h5ad_path = safe_value(hrow.get("h5ad_path", ""))

                if sample_id:
                    sample_node = f"sample::{dataset_id}::{sample_id}"
                    add_node(
                        graph,
                        sample_node,
                        sample_id,
                        "Sample",
                        f"<b>Sample</b><br>{sample_id}<br>Dataset: {dataset_id}",
                    )
                    add_edge(graph, dataset_node, sample_node, "contains sample")

                    if h5ad_path:
                        h5ad_label = Path(h5ad_path).name
                        h5ad_node = f"h5ad::{dataset_id}::{sample_id}"
                        add_node(
                            graph,
                            h5ad_node,
                            h5ad_label[:45] + "..." if len(h5ad_label) > 45 else h5ad_label,
                            "H5AD file",
                            f"<b>H5AD file</b><br>{h5ad_path}",
                        )
                        add_edge(graph, sample_node, h5ad_node, "has H5AD file")

    return graph


def make_legend_html(enabled_groups):
    rows = []
    for group in enabled_groups:
        if group not in GROUP_STYLES:
            continue
        color = GROUP_STYLES[group]["color"]
        rows.append(
            f"""
            <div style="display:flex;align-items:center;margin-bottom:8px;">
                <span style="
                    display:inline-block;
                    width:12px;
                    height:12px;
                    border-radius:50%;
                    background:{color};
                    margin-right:10px;
                    box-shadow:0 0 8px {color};
                "></span>
                <span style="color:#EAEAEA;font-size:13px;">{group}</span>
            </div>
            """
        )
    return "".join(rows)


def export_graph_to_html(
    graph: nx.Graph,
    enabled_groups,
    gravity=-90,
    spring_length=140,
    central_gravity=0.02,
):
    REPORTS_DIR.mkdir(exist_ok=True)

    net = Network(
        height="820px",
        width="100%",
        bgcolor="#050816",
        font_color="#EAEAEA",
        notebook=False,
        cdn_resources="in_line",
    )

    net.from_nx(graph)

    net.set_options(
        f"""
        {{
          "nodes": {{
            "shadow": {{
              "enabled": true,
              "color": "rgba(125, 220, 255, 0.35)",
              "size": 16,
              "x": 0,
              "y": 0
            }},
            "font": {{
              "color": "#EAEAEA",
              "strokeWidth": 3,
              "strokeColor": "#050816"
            }}
          }},
          "edges": {{
            "color": {{
              "color": "rgba(180, 220, 255, 0.18)",
              "highlight": "#7FDBFF",
              "hover": "#FFD166"
            }},
            "smooth": {{
              "enabled": true,
              "type": "continuous"
            }},
            "shadow": {{
              "enabled": true,
              "color": "rgba(125, 220, 255, 0.10)",
              "size": 6,
              "x": 0,
              "y": 0
            }}
          }},
          "physics": {{
            "enabled": true,
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {{
              "gravitationalConstant": {gravity},
              "centralGravity": {central_gravity},
              "springLength": {spring_length},
              "springConstant": 0.08,
              "damping": 0.55,
              "avoidOverlap": 0.9
            }},
            "stabilization": {{
              "enabled": true,
              "iterations": 220
            }}
          }},
          "interaction": {{
            "hover": true,
            "tooltipDelay": 60,
            "navigationButtons": true,
            "keyboard": true,
            "hideEdgesOnDrag": false
          }}
        }}
        """
    )

    net.write_html(str(GRAPH_HTML_PATH), notebook=False)
    html = GRAPH_HTML_PATH.read_text(encoding="utf-8")

    legend_html = make_legend_html(enabled_groups)

    custom_overlay = f"""
    <style>
    body {{
        margin: 0;
        background: radial-gradient(circle at center, #0F1E3A 0%, #091122 42%, #050816 100%);
        overflow: hidden;
        font-family: Arial, sans-serif;
    }}

    #mynetwork {{
        background: radial-gradient(circle at center, #0F1E3A 0%, #091122 42%, #050816 100%) !important;
        border: 1px solid rgba(125, 220, 255, 0.14);
        border-radius: 18px;
        box-shadow: 0 0 28px rgba(125, 220, 255, 0.12);
    }}

    .vis-tooltip {{
        background: rgba(8, 14, 28, 0.96) !important;
        color: #EAEAEA !important;
        border: 1px solid rgba(125, 220, 255, 0.45) !important;
        border-radius: 10px !important;
        padding: 10px !important;
        box-shadow: 0 0 16px rgba(125, 220, 255, 0.18) !important;
        font-size: 12px !important;
    }}

    .graph-legend {{
        position: absolute;
        top: 14px;
        left: 14px;
        z-index: 9999;
        width: 220px;
        padding: 14px 14px 10px 14px;
        border-radius: 14px;
        background: rgba(7, 12, 24, 0.78);
        border: 1px solid rgba(125, 220, 255, 0.12);
        backdrop-filter: blur(10px);
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.25);
    }}

    .graph-legend-title {{
        color: #EAEAEA;
        font-size: 15px;
        font-weight: 700;
        margin-bottom: 12px;
    }}
    </style>

    <div class="graph-legend">
        <div class="graph-legend-title">Knowledge Graph Legend</div>
        {legend_html}
    </div>
    """

    html = html.replace("</head>", custom_overlay + "\n</head>")
    GRAPH_HTML_PATH.write_text(html, encoding="utf-8")

    return GRAPH_HTML_PATH


def generate_knowledge_graph_html(
    enabled_groups=None,
    focus_dataset=None,
    include_h5ad=False,
    max_h5ad_per_dataset=5,
    gravity=-90,
    spring_length=140,
    central_gravity=0.02,
):
    datasets_df = load_datasets()
    h5ad_df = load_h5ad_files()

    if datasets_df.empty:
        return {
            "success": False,
            "message": "No datasets found in SQLite database.",
            "html_path": None,
            "n_nodes": 0,
            "n_edges": 0,
        }

    if enabled_groups is None:
        enabled_groups = list(GROUP_STYLES.keys())

    graph = build_graph(
        datasets_df=datasets_df,
        h5ad_df=h5ad_df,
        enabled_groups=enabled_groups,
        focus_dataset=focus_dataset,
        include_h5ad=include_h5ad,
        max_h5ad_per_dataset=max_h5ad_per_dataset,
    )

    html_path = export_graph_to_html(
        graph=graph,
        enabled_groups=enabled_groups,
        gravity=gravity,
        spring_length=spring_length,
        central_gravity=central_gravity,
    )

    return {
        "success": True,
        "message": "Knowledge graph generated.",
        "html_path": str(html_path),
        "n_nodes": graph.number_of_nodes(),
        "n_edges": graph.number_of_edges(),
        "available_groups": list(GROUP_STYLES.keys()),
        "available_datasets": sorted(datasets_df["dataset_id"].astype(str).unique().tolist()),
    }
