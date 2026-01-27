import pandas as pd
import requests
import json
from typing import List, Dict
import os

WORKER_URL = os.getenv("AI_CLASSIFIER_URL")  # set to 'http://127.0.0.1:8787/' to use a local worker
BATCH_SIZE = 10
DESCRIPTION_WORD_LIMIT = 400  # truncate descriptions to ~400 words


# -------------------------------------------
# Truncate job description
# -------------------------------------------
def truncate_description(text: str, limit: int = DESCRIPTION_WORD_LIMIT) -> str:
    words = text.split()
    if len(words) <= limit:
        return text
    return " ".join(words[:limit])


# -------------------------------------------
# Main batch classifier
# -------------------------------------------
def classify_jobs_ai(df: pd.DataFrame, batch_size: int = BATCH_SIZE, verbose=True) -> pd.DataFrame:
    df = df.copy()

    # Ensure required fields exist
    for col in ["title", "description"]:
        if col not in df.columns:
            df[col] = ""

    # Truncate descriptions to save neurons
    df["description_trunc"] = df["description"].fillna("").apply(truncate_description)

    results: List[Dict] = []
    total_jobs = len(df)

    if verbose:
        print(f"Classifying {total_jobs} jobs using AI Worker in batches of {batch_size}...")

    # Loop through batches
    for start in range(0, total_jobs, batch_size):
        end = min(start + batch_size, total_jobs)
        batch = df.iloc[start:end]

        payload = [
            {"title": row["title"], "description": row["description_trunc"]}
            for _, row in batch.iterrows()
        ]

        try:
            resp = requests.post(WORKER_URL, json={"jobs": payload}, timeout=10000)
            resp.raise_for_status()
            data = resp.json()

            if "results" not in data:
                raise ValueError(f"No 'results' returned from Worker: {data}")

            # Process each job result
            for r in data["results"]:
                role_scores = r.get("role") or r.get("role_scores") or {}
                seniority_scores = r.get("seniority_scores") or {}
                skills = r.get("skills") or []
                summary = r.get("summary") or ""

                results.append({
                    "role_scores": role_scores,
                    "seniority_scores": seniority_scores,
                    "skills": skills,
                    "summary": summary,
                })

            if verbose:
                print(f"✓ Completed batch {start}-{end}")

        except Exception as e:
            print(f"⚠️ Batch {start}-{end} failed: {e}")
            results.extend([
                {
                    "role_scores": {},
                    "seniority_scores": {},
                    "skills": [],
                    "summary": "",
                }
            ] * len(payload))

    # Ensure alignment of results and dataframe size
    if len(results) != total_jobs:
        print("⚠️ Result count mismatch. Padding unknown scores.")
        while len(results) < total_jobs:
            results.append({
                "role_scores": {},
                "seniority_scores": {},
                "skills": [],
                "summary": "",
            })

    # Apply results to dataframe
    df["role_scores"] = [json.dumps(r["role_scores"]) for r in results]
    df["seniority_scores"] = [json.dumps(r["seniority_scores"]) for r in results]
    df["skills"] = [json.dumps(r["skills"]) for r in results]
    df["summary"] = [r["summary"] for r in results]

    # Filter out 'mid and above' jobs
    def is_mid_and_above(scores_str):
        try:
            scores = json.loads(scores_str)
            # Normalize key for safety
            scores = {k.lower().strip(): v for k, v in scores.items()}
            return scores.get('mid and above', 0) == 1
        except (json.JSONDecodeError, AttributeError):
            return False

    discard_mask = df['seniority_scores'].apply(is_mid_and_above)
    discarded_df = df[discard_mask].copy()
    kept_df = df[~discard_mask].copy()

    if not discarded_df.empty:
        output_path = 'ai-discarded_jobs.csv'
        if verbose:
            print(f"Saving {len(discarded_df)} discarded jobs to {output_path}...")
        try:
            # Append to the CSV if it exists, otherwise create it
            header = not os.path.exists(output_path)
            discarded_df.to_csv(output_path, mode='a', header=header, index=False)
        except Exception as e:
            print(f"⚠️ Failed to save discarded jobs: {e}")

    if verbose:
        print(f"Returning {len(kept_df)} jobs to be saved.")

    return kept_df
