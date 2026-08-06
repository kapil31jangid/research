"""Export a simulated experiment summary as a Markdown comparison table."""
import argparse
from pathlib import Path
import pandas as pd
def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--input", type=Path, default=Path("data/experiments/latest/summary.csv")); parser.add_argument("--output", type=Path, default=Path("data/experiments/latest/export.md")); args = parser.parse_args(); frame = pd.read_csv(args.input); args.output.write_text("# Simulated experiment export\n\n```csv\n" + frame.to_csv(index=False) + "```\n", encoding="utf-8")
if __name__ == "__main__": main()
