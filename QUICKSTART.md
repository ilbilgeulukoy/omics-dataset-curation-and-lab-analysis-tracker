# Quickstart

This file explains how to install and run the Omics Dataset Curation and Lab Analysis Tracker from zero.

A normal user should install the project from GitHub using `git clone`.

No manual folder creation or manual file copying is required.

## 1. Clone the repository

Open a terminal and go to the folder where you want to keep the project.

Example:

    cd ~/Desktop

Clone the repository:

    git clone https://github.com/ilbilgeulukoy/omics-dataset-curation-and-lab-analysis-tracker.git

Enter the project folder:

    cd omics-dataset-curation-and-lab-analysis-tracker

## 2. Create a Python environment

Run:

    python3 -m venv .venv

Activate it:

    source .venv/bin/activate

You should now see `.venv` in the terminal prompt.

The `.venv` folder is a local Python environment. It stores the packages needed by this project on your own computer. It is not uploaded to GitHub.

## 3. Install dependencies

Run:

    python -m pip install --upgrade pip

    python -m pip install -r requirements.txt

## 4. Run with demo data

You can test the app without adding your own dataset files.

The project includes demo data:

    data/mock_datasets.csv

Run:

    python scripts/import_csv_to_sqlite.py

    python scripts/export_datasets_to_obsidian.py

    python scripts/index_obsidian_notes_to_sqlite.py

    streamlit run app.py

Open the URL shown by Streamlit.

Usually:

    http://localhost:8501

## 5. Use your own datasets

To use real project or lab data, fill the CSV templates.

Templates are in:

    templates/

The main file is:

    templates/datasets_template.csv

After filling it, save it as:

    data/datasets.csv

Optional files:

    data/sample_metadata.csv
    data/qc_summary.csv
    data/sample_h5ad_paths.csv

Then rebuild the local registry:

    python scripts/import_csv_to_sqlite.py

    python scripts/export_datasets_to_obsidian.py

    python scripts/index_obsidian_notes_to_sqlite.py

    streamlit run app.py

## 6. What the scripts do

Import CSV files into SQLite:

    python scripts/import_csv_to_sqlite.py

Export markdown curation notes:

    python scripts/export_datasets_to_obsidian.py

Index notes for retrieval:

    python scripts/index_obsidian_notes_to_sqlite.py

Launch the dashboard:

    streamlit run app.py

## 7. What appears after running

The app creates:

    data/omics_tracker.db

This is the local SQLite database.

It also creates or updates:

    obsidian_vault/

This folder contains markdown curation notes.

It also creates:

    reports/knowledge_graph.html

This file is used by the Knowledge Graph tab.

## 8. Common problems

### streamlit command not found

Make sure the environment is activated:

    source .venv/bin/activate

Then reinstall dependencies:

    python -m pip install -r requirements.txt

### No dataset appears

Run:

    python scripts/import_csv_to_sqlite.py

If you do not have `data/datasets.csv`, the app should use:

    data/mock_datasets.csv

### Curation Assistant has no results

Run:

    python scripts/export_datasets_to_obsidian.py

    python scripts/index_obsidian_notes_to_sqlite.py

### The app opens but data is old

Re-run all update scripts:

    python scripts/import_csv_to_sqlite.py

    python scripts/export_datasets_to_obsidian.py

    python scripts/index_obsidian_notes_to_sqlite.py

Then restart Streamlit.

## 9. Minimal command sequence

For a first demo run:

    cd ~/Desktop
    git clone https://github.com/ilbilgeulukoy/omics-dataset-curation-and-lab-analysis-tracker.git
    cd omics-dataset-curation-and-lab-analysis-tracker
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    python scripts/import_csv_to_sqlite.py
    python scripts/export_datasets_to_obsidian.py
    python scripts/index_obsidian_notes_to_sqlite.py
    streamlit run app.py

## 10. Manual CSV curation note

The dataset CSV is intentionally curated by a human.

Public omics metadata is often incomplete or inconsistent, so fully automatic curation is not always reliable.

The manual part is:

    fill dataset metadata once in CSV format

The automatic part is:

    SQLite registry
    Obsidian notes
    searchable curation assistant
    Streamlit dashboard
    knowledge graph

This design keeps the system transparent and easy to verify.
