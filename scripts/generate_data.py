import argparse
import json
from pathlib import Path
import pandas as pd
from app.generators.master_generator import generate_master_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--students", type=int, default=20)
    parser.add_argument("--buses", type=int, default=5)
    parser.add_argument("--stops", type=int, default=10)
    parser.add_argument("--zones", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20261022)
    args = parser.parse_args()

    output = Path("data/generated")
    output.mkdir(parents=True, exist_ok=True)
    data = generate_master_data(args.students, args.buses, args.stops, args.zones, args.seed)
    for name, rows in data.items():
        pd.DataFrame(rows).to_csv(output / f"{name}.csv", index=False)
    manifest = {
        "seed": args.seed, "students": args.students, "buses": args.buses,
        "stops": args.stops, "zones": args.zones,
        "row_counts": {name: len(rows) for name, rows in data.items()},
        "generator_version": "0.1.0"
    }
    (output / "generation_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
