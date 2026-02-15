#!/usr/bin/env python3
"""
Generate a synthetic CSV dataset with many symptom columns.
Usage examples:
  python3 generate_sample_dataset.py --symptoms 1000 --rows 2000 --out sample_large.csv
  python3 generate_sample_dataset.py --symptoms 2000 --rows 500 --diseases Flu,Dengue,Cold
"""
import csv
import argparse
import random
import sys

DEFAULT_DISEASES = [
    "Flu", "Dengue", "Common Cold", "Migraine", "Fatigue Syndrome",
    "Bronchial Asthma", "Malaria", "Pneumonia", "Allergy", "Typhoid",
    "Hepatitis A", "Muscle Pain", "No Disease"
]


def generate(symptoms_count: int, rows: int, out_path: str, diseases, prevalence: float, seed: int, per_disease: int = 0):
    random.seed(seed)

    symptom_names = [f"symptom_{i:04d}" for i in range(1, symptoms_count + 1)]

    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        # header
        writer.writerow(symptom_names + ["Disease"])

        if per_disease and per_disease > 0:
            # Balanced generation: exactly `per_disease` rows per disease
            total = per_disease * len(diseases)
            for disease in diseases:
                for _ in range(per_disease):
                    # For realism, vary per-row base symptom probability slightly
                    row_prev = max(0.001, min(0.95, random.gauss(prevalence, 0.03)))
                    row = ["1" if random.random() < row_prev else "0" for _ in range(symptoms_count)]
                    writer.writerow(row + [disease])
            print(f"Wrote {total} rows x {symptoms_count} symptoms to {out_path} (balanced: {per_disease} per disease)")
            return

        for r in range(rows):
            # For realism, vary per-row base symptom probability slightly
            row_prev = max(0.001, min(0.95, random.gauss(prevalence, 0.03)))
            row = ["1" if random.random() < row_prev else "0" for _ in range(symptoms_count)]

            # Simple disease assignment: pick randomly (could be made rule-based)
            disease = random.choice(diseases)
            writer.writerow(row + [disease])

    print(f"Wrote {rows} rows x {symptoms_count} symptoms to {out_path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Generate synthetic symptom dataset CSV")
    p.add_argument("--symptoms", "-s", type=int, default=1000, help="Number of symptom columns to generate")
    p.add_argument("--rows", "-r", type=int, default=1000, help="Number of rows (examples) to generate")
    p.add_argument("--out", "-o", default="sample_dataset_large.csv", help="Output CSV path")
    p.add_argument("--diseases", "-d", default=",".join(DEFAULT_DISEASES), help="Comma-separated disease labels to use")
    p.add_argument("--prevalence", type=float, default=0.05, help="Base prevalence for symptoms (0-1)")
    p.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    p.add_argument("--per-disease", "-p", type=int, default=0, help="If set, generate this many examples per disease (balanced)")

    args = p.parse_args()

    diseases = [x.strip() for x in args.diseases.split(",") if x.strip()]
    if not diseases:
        print("No diseases provided. Exiting.")
        sys.exit(1)

    generate(args.symptoms, args.rows, args.out, diseases, args.prevalence, args.seed, per_disease=args.per_disease)
