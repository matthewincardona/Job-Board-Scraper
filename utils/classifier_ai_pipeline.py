import pandas as pd
import requests
import json
from typing import List, Dict

WORKER_URL = "http://127.0.0.1:8787/"
BATCH_SIZE = 50


# -------------------------------------------
# Choose highest scoring key
# -------------------------------------------
def choose_top_scoring(scores: Dict[str, float], fallback: str) -> str:
    if not scores:
        return fallback
    return max(scores.items(), key=lambda x: x[1])[0]


# -------------------------------------------
# Main batch classifier
# -------------------------------------------
def classify_jobs_ai(df: pd.DataFrame, batch_size: int = BATCH_SIZE, verbose=True) -> pd.DataFrame:
    df = df.copy()

    # Ensure required fields exist
    for col in ["title", "description"]:
        if col not in df.columns:
            df[col] = ""

    results: List[Dict] = []
    total_jobs = len(df)

    if verbose:
        print(f"Classifying {total_jobs} jobs using AI Worker in batches of {batch_size}...")

    # Loop through batches
    for start in range(0, total_jobs, batch_size):
        end = start + batch_size
        batch = df.iloc[start:end]

        payload = [
            {"title": row["title"], "description": row["description"]}
            for _, row in batch.iterrows()
        ]

        try:
            resp = requests.post(WORKER_URL, json={"jobs": payload}, timeout=60)
            resp.raise_for_status()
            data = resp.json()

            if "results" not in data:
                raise ValueError(f"No 'results' returned from Worker: {data}")

            # Process each job result
            for r in data["results"]:
                role_scores = r.get("role_scores", {})
                seniority_scores = r.get("seniority_scores", {})

                results.append({
                    "role_scores": role_scores,
                    "seniority_scores": seniority_scores,
                    "ux_category": choose_top_scoring(role_scores, "other"),
                    "seniority": choose_top_scoring(seniority_scores, "unknown"),
                })

        except Exception as e:
            print(f"⚠️ Batch {start}-{end} failed: {e}")
            results.extend([
                {
                    "role_scores": {},
                    "seniority_scores": {},
                    "ux_category": "other",
                    "seniority": "unknown"
                }
            ] * len(payload))

    # Ensure alignment of results and dataframe size
    if len(results) != total_jobs:
        print("⚠️ Result count mismatch. Padding unknown scores.")
        while len(results) < total_jobs:
            results.append({
                "role_scores": {},
                "seniority_scores": {},
                "ux_category": "other",
                "seniority": "unknown"
            })

    # Apply results to dataframe
    df["role_scores"] = [json.dumps(r["role_scores"]) for r in results]
    df["seniority_scores"] = [json.dumps(r["seniority_scores"]) for r in results]
    df["ux_category"] = [r["ux_category"] for r in results]
    df["seniority"] = [r["seniority"] for r in results]

    return df
