# Omics Dataset Curation & Lab Analysis Tracker

A Streamlit-based dashboard for curating omics datasets, validating standardized CSV manifests, tracking analysis-ready files, and ranking scRNA-seq dataset combinations based on exact common gene overlap, total patient count, and total cell count.

This project was designed as a bioinformatics portfolio project combining dataset curation, lab workflow tracking, single-cell analysis metadata management, and integration planning.

## Project Goals

The dashboard helps researchers track omics datasets across different analysis stages:

- Dataset curation
- Sample-level metadata tracking
- H5AD file manifest validation
- QC / preprocessing report tracking
- scRNA-seq dataset combination planning
- CSV export for downstream analysis

The project is designed to support multiple omics assay types:

- scRNA-seq
- Spatial transcriptomics
- Bulk RNA-seq
- Proteomics
- qPCR

## Main Features

### Dataset Registry Dashboard

The dashboard displays a standardized dataset registry with dataset name, assay type, disease area, species, platform, patient count, sample count, cell or spot count, gene count, data access status, verification status, analysis inclusion status, primary data path, metadata path, and QC report path.

### CSV Format Guide

The app includes an internal CSV format guide describing required columns, recommended columns, valid assay types, and assay-specific optional columns.

### CSV Templates

Reusable templates are provided in the templates/ folder:

    templates/datasets_template.csv
    templates/sample_metadata_template.csv
    templates/qc_summary_template.csv
    templates/sample_h5ad_paths_template.csv

Users can copy these templates, fill them manually, and save the completed files into the data/ folder.

### Dataset Combination Optimizer

The scRNA-seq combination optimizer uses preprocessing-passed H5AD sample files.

It computes:

- Exact common gene intersection from adata.var_names
- Total number of patients
- Total number of cells
- Total number of samples

Ranking is performed without artificial scores or heuristic penalties:

1. Highest total patient count
2. Highest number of common genes
3. Highest total cell count

## Project Structure

    omics-dataset-curation-and-lab-analysis-tracker/
    ├── app.py
    ├── requirements.txt
    ├── README.md
    ├── .gitignore
    ├── data/
    │   └── mock_datasets.csv
    ├── templates/
    │   ├── datasets_template.csv
    │   ├── sample_metadata_template.csv
    │   ├── qc_summary_template.csv
    │   └── sample_h5ad_paths_template.csv
    ├── src/
    │   ├── schema.py
    │   ├── validation.py
    │   ├── combination.py
    │   ├── database.py
    │   ├── crud.py
    │   ├── models.py
    │   ├── plots.py
    │   └── utils.py
    ├── scripts/
    │   └── convert_combi_txt_to_manifest.py
    ├── reports/
    ├── screenshots/
    └── api/
        └── main.py

## Installation

Clone the repository:

    git clone https://github.com/YOUR_USERNAME/omics-dataset-curation-and-lab-analysis-tracker.git
    cd omics-dataset-curation-and-lab-analysis-tracker

Create a Python environment.

Using venv:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

Or using conda:

    conda create -n omics-tracker python=3.11
    conda activate omics-tracker
    pip install -r requirements.txt

Run the app:

    streamlit run app.py

Open the local URL shown in the terminal, usually:

    http://localhost:8501

## Input Files

### Dataset Registry

The main dataset registry should follow this format:

    dataset_id,dataset_name,assay_type,disease_area,species,platform,n_patients,n_samples,n_cells_or_spots,n_genes,data_level,data_access,verified,include_for_analysis,primary_data_path,metadata_path,qc_report_path,notes
    SC001,example_scRNA_dataset,scRNA-seq,ovarian cancer,human,10x Genomics,6,18,76000,19750,h5ad,public,yes,yes,path/to/file.h5ad,path/to/metadata.csv,path/to/qc_report.html,example dataset
    SP001,example_spatial_dataset,spatial,ovarian cancer,human,10x Visium,4,12,55000,18000,spatial_folder,local_only,yes,yes,path/to/spatial_folder,path/to/spatial_metadata.csv,path/to/spatial_qc.html,example spatial dataset

Required columns:

    dataset_id
    dataset_name
    assay_type
    disease_area
    species
    primary_data_path
    verified
    include_for_analysis

Valid assay types:

    scRNA-seq
    spatial
    bulk RNA-seq
    proteomics
    qPCR

### H5AD Sample Manifest

For the combination optimizer, provide a sample-level H5AD manifest:

    dataset_id,dataset_name,sample_id,h5ad_path
    sample,year_author,dataset_name,/server/path/to/sample_dataset_id/file.h5ad

Each row represents one preprocessing-passed H5AD sample file.

The optimizer requires that these H5AD paths are accessible from the machine where the app is running.

## Converting a TXT List of H5AD Paths

If you have a text file containing one H5AD path per line, save it as:

    data/combi_final.txt

Example content:

    /data/project/dataset_1/sample_A/file.h5ad
    /data/project/dataset_1/sample_B/file.h5ad
    /data/project/dataset_2/sample_C/file.h5ad

Then run:

    python scripts/convert_combi_txt_to_manifest.py

This creates:

    data/sample_h5ad_paths.csv

The generated CSV can be edited manually if needed.

## Running on a Server or HPC Environment

This dashboard can be run directly on the server where the H5AD files are stored. This is recommended for the exact dataset combination optimizer.

### 1. Clone the repository on the server

    git clone https://github.com/YOUR_USERNAME/omics-dataset-curation-and-lab-analysis-tracker.git
    cd omics-dataset-curation-and-lab-analysis-tracker

### 2. Create an environment

Using conda:

    conda create -n omics-tracker python=3.11
    conda activate omics-tracker
    pip install -r requirements.txt

Or using venv:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

### 3. Prepare input files

Copy the templates:

    cp templates/datasets_template.csv data/datasets.csv
    cp templates/sample_h5ad_paths_template.csv data/sample_h5ad_paths.csv
    cp templates/qc_summary_template.csv data/qc_summary.csv

Edit data/sample_h5ad_paths.csv so that each h5ad_path points to a real file on the server.

### 4. Run Streamlit on the server

    streamlit run app.py --server.address 127.0.0.1 --server.port 8501

### 5. Open the app locally using SSH tunneling

On your local computer, open a new terminal:

    ssh -L 8501:localhost:8501 USERNAME@SERVER_ADDRESS

Then open your browser:

    http://localhost:8501

The app runs on the server, while the interface is accessed from your local browser.

## Example Server Workflow

    ssh USERNAME@SERVER_ADDRESS

    git clone https://github.com/YOUR_USERNAME/omics-dataset-curation-and-lab-analysis-tracker.git
    cd omics-dataset-curation-and-lab-analysis-tracker

    conda create -n omics-tracker python=3.11
    conda activate omics-tracker
    pip install -r requirements.txt

    cp /path/to/combi_final.txt data/combi_final.txt
    python scripts/convert_combi_txt_to_manifest.py

    streamlit run app.py --server.address 127.0.0.1 --server.port 8501

On your local machine:

    ssh -L 8501:localhost:8501 USERNAME@SERVER_ADDRESS

Open:

    http://localhost:8501

## Notes on Large H5AD Files

The exact combination optimizer reads H5AD files to extract:

- adata.var_names
- adata.n_obs

For large datasets or hundreds of H5AD files, this step can be slow. In future versions, a cache-building script can be added to precompute dataset-level gene sets and cell counts once, then reuse them during dashboard sessions.
