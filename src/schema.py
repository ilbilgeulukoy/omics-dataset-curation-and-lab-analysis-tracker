REQUIRED_COLUMNS = [
    "dataset_id",
    "dataset_name",
    "assay_type",
    "disease_area",
    "species",
    "primary_data_path",
    "verified",
    "include_for_analysis",
]

RECOMMENDED_COLUMNS = [
    "platform",
    "n_patients",
    "n_samples",
    "n_cells_or_spots",
    "n_genes",
    "data_level",
    "data_access",
    "metadata_path",
    "qc_report_path",
    "notes",
]

ASSAY_SPECIFIC_COLUMNS = {
    "scRNA-seq": [
        "sample_col",
        "patient_col",
        "cell_type_col",
        "condition_col",
        "h5ad_path",
    ],
    "spatial": [
        "platform",
        "spatial_unit",
        "image_available",
        "coordinates_available",
        "segmentation_status",
        "annotation_status",
        "slide_id",
        "capture_area",
    ],
    "bulk RNA-seq": [
        "count_matrix_path",
        "metadata_path",
        "condition_col",
        "batch_col",
    ],
    "proteomics": [
        "protein_matrix_path",
        "metadata_path",
        "condition_col",
    ],
    "qPCR": [
        "ct_table_path",
        "target_gene_col",
        "reference_gene_col",
    ],
}

VALID_ASSAY_TYPES = [
    "scRNA-seq",
    "spatial",
    "bulk RNA-seq",
    "proteomics",
    "qPCR",
]
