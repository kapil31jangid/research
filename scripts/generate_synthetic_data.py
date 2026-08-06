"""Generate reproducible simulated interactions; not real learner data."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

PROFILES = {"fast_learner": (0.65, .15, .08, .02), "slow_learner": (.30, .06, .12, .04), "high_guessing": (.35, .10, .08, .30), "high_slip": (.50, .10, .25, .03), "frequent_forgetting": (.50, .10, .10, .12), "misconception_prone": (.40, .09, .12, .05), "intermittent_user": (.45, .09, .10, .06), "low_resource_device": (.45, .09, .12, .05)}
def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--learners", type=int, default=1000); parser.add_argument("--interactions", type=int, default=50); parser.add_argument("--seed", type=int, default=42); parser.add_argument("--output", type=Path, default=Path("data/synthetic")); args = parser.parse_args(); rng = np.random.default_rng(args.seed); rows = []
    profiles = list(PROFILES)
    for learner_index in range(args.learners):
        profile = profiles[learner_index % len(profiles)]; mastery, learning, slip, forgetting = PROFILES[profile]
        for attempt in range(args.interactions):
            resource = rng.uniform(.12, .5) if profile == "low_resource_device" else rng.uniform(.4, 1)
            days = rng.exponential(3 if profile == "intermittent_user" else 1); retained = mastery * np.exp(-forgetting * days); difficulty = int(rng.integers(1, 4)); misconception = float(rng.uniform() < (.35 if profile == "misconception_prone" else .08)); chance = np.clip(retained - .12 * (difficulty - 1) + .08 * (resource - .5) - .12 * misconception, .03, .97); correct = int(rng.random() < chance); mastery = np.clip(mastery + learning * (1 - mastery) if correct else mastery * (1 - slip), .01, .99)
            rows.append({"learner_id": f"synthetic_{learner_index:04d}", "profile": profile, "mastery": mastery, "retained_mastery": retained, "uncertainty": 1 / np.sqrt(attempt + 1), "question_difficulty": difficulty, "concept_difficulty": difficulty, "recent_correctness": chance, "average_response_time": float(rng.lognormal(1.0, .4)), "response_time_variation": float(rng.uniform(0, .8)), "hint_usage_rate": float(rng.uniform(0, .7)), "attempts": attempt + 1, "correct_attempts": int((attempt + 1) * chance), "prerequisite_mastery": float(np.clip(mastery + rng.normal(0, .1), 0, 1)), "days_since_practice": days, "misconception_confidence": misconception, "resource_score": resource, "correct": correct, "offline": bool(rng.random() < (.3 if profile == "low_resource_device" else .08))})
    frame = pd.DataFrame(rows); args.output.mkdir(parents=True, exist_ok=True); frame.to_csv(args.output / "interactions.csv", index=False); frame.to_parquet(args.output / "interactions.parquet", index=False); print(f"Generated {len(frame)} simulated interactions for {args.learners} learners.")
if __name__ == "__main__": main()
