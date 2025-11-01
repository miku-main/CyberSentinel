from pathlib import Path
from app.data.generator import generate_dataset

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    csv_path = root / "demos" / "traffic_small.csv"
    json_path = root / "demos" / "attacks_scenarios.json"
    generate_dataset(csv_path, json_path)
    print(f"Wrote demo files to: {csv_path.parent}")