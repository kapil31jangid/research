"""Train and evaluate optional logistic-regression response model on synthetic data."""
import argparse, json, sys
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.learner_model.response_predictor import evaluate_predictor, save_predictor, train_predictor
def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--data", type=Path, default=Path("data/synthetic/interactions.parquet")); parser.add_argument("--model", type=Path, default=Path("data/models/response_predictor.joblib")); parser.add_argument("--metrics", type=Path, default=Path("data/models/response_predictor_metrics.json")); args = parser.parse_args(); frame = pd.read_parquet(args.data); train, holdout = train_test_split(frame, test_size=.3, random_state=42, stratify=frame["correct"]); validation, test = train_test_split(holdout, test_size=.5, random_state=42, stratify=holdout["correct"]); model = train_predictor(train); metrics = {"validation": evaluate_predictor(model, validation), "test": evaluate_predictor(model, test), "model_version": "0.1.0", "data": str(args.data)}; save_predictor(model, args.model); args.metrics.parent.mkdir(parents=True, exist_ok=True); args.metrics.write_text(json.dumps(metrics, indent=2), encoding="utf-8"); print(json.dumps(metrics, indent=2))
if __name__ == "__main__": main()
