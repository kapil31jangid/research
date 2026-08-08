import json

from app.evaluation.config import ExperimentConfig
from app.evaluation.simulator import run_experiment
from app.evaluation.synthetic_learners import generate_learners


def test_synthetic_learners_are_seed_deterministic() -> None:
    distribution = {"mixed": 1.0}
    first = generate_learners(2, ["whole_numbers"], 7, distribution)
    assert first == generate_learners(2, ["whole_numbers"], 7, distribution)
    assert first != generate_learners(2, ["whole_numbers"], 8, distribution)


def test_smoke_experiment_writes_reproducible_artifacts(tmp_path) -> None:
    config = ExperimentConfig(
        experiment_name="test",
        random_seed=7,
        learner_count=2,
        interactions_per_learner=3,
        output_dir=str(tmp_path / "artifacts"),
        learner_profile_distribution={"mixed": 1.0},
    )
    directory = run_experiment(config)
    assert (directory / "interactions.parquet").exists()
    assert (directory / "interactions.csv").exists()
    assert json.loads((directory / "summary.json").read_text())["simulated_results"] is True
    assert json.loads((directory / "provenance.json").read_text())["git_commit_sha"]
