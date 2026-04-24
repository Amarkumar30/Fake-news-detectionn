from __future__ import annotations

import argparse
import json

from model_service import LiarModelTrainer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train and persist LIAR fake news detection models.")
    parser.add_argument("--data-dir", type=str, default=None, help="Directory containing train.tsv, valid.tsv, and test.tsv.")
    parser.add_argument("--models-dir", type=str, default=None, help="Directory where trained joblib artifacts will be stored.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    trainer = LiarModelTrainer(models_dir=args.models_dir)
    summary = trainer.train_and_persist(data_dir=args.data_dir)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
