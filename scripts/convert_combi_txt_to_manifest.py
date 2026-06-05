from pathlib import Path
import pandas as pd


def infer_dataset_name(path_str: str) -> str:
    parts = Path(path_str).parts
    if "data" in parts:
        data_indices = [i for i, part in enumerate(parts) if part == "data"]
        for idx in reversed(data_indices):
            if idx + 1 < len(parts):
                candidate = parts[idx + 1]
                if candidate[:4].isdigit() or "_" in candidate:
                    return candidate
    return "unknown_dataset"


def infer_sample_id(path_str: str) -> str:
    parts = Path(path_str).parts
    for part in parts:
        if part.startswith("sample_"):
            return part.replace("sample_", "")
    return Path(path_str).stem


input_path = Path("data/combi_final.txt")
output_path = Path("data/sample_h5ad_paths.csv")

if not input_path.exists():
    raise FileNotFoundError("data/combi_final.txt not found")

rows = []
for line in input_path.read_text().splitlines():
    h5ad_path = line.strip()
    if not h5ad_path or h5ad_path.startswith("#"):
        continue

    dataset_name = infer_dataset_name(h5ad_path)
    rows.append({
        "dataset_id": dataset_name,
        "dataset_name": dataset_name,
        "sample_id": infer_sample_id(h5ad_path),
        "h5ad_path": h5ad_path,
    })

df = pd.DataFrame(rows)
df.to_csv(output_path, index=False)

print(f"Created {output_path} with {len(df)} rows")
print(df.head())
