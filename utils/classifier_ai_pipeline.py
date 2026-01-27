import pandas as pd
import requests
import json
from typing import Dict, Any, List
from tqdm import tqdm

# -------------------------------------------
# Configuration
# -------------------------------------------
BASE_WORKER_URL = "http://127.0.0.1:8787"
DESCRIPTION_WORD_LIMIT = 400
REQUEST_TIMEOUT = 60

TAG_TO_CLASSIFIER_MAP = {
    "possible_ux_product": {
        "endpoint": "/classify-ux-product",
        "category": "UX/Product Design"
    },
    "possible_frontend": {
        "endpoint": "/classify-frontend",
        "category": "Frontend/UXE"
    },
    # "possible_creative": {
    #     "endpoint": "/classify-creative",
    #     "category": "Creative/Design"
    # },
}

# -------------------------------------------
# Helper Functions
# -------------------------------------------
def truncate_description(text: str, limit: int = DESCRIPTION_WORD_LIMIT) -> str:
    """Truncates text to a specified word limit."""
    if not isinstance(text, str):
        return ""
    words = text.split()
    return " ".join(words[:limit]) if len(words) > limit else text


def validate_worker_connection() -> bool:
    """Check if AI worker is accessible."""
    try:
        resp = requests.get(f"{BASE_WORKER_URL}/health", timeout=5)
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"✗ Cannot reach AI worker at {BASE_WORKER_URL}: {e}")
        return False


def call_classifier(endpoint: str, job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls a specific classifier endpoint on the AI worker with a single job.
    
    Returns:
        A dictionary with the classifier's results (is_match, seniority, etc.).
        Returns a default 'no match' structure on failure.
    """
    try:
        url = f"{BASE_WORKER_URL}{endpoint}"
        resp = requests.post(url, json={"job": job}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"⚠️  Classifier request failed for {endpoint}: {e}")
        return {"is_match": False}


# -------------------------------------------
# Main Classification Orchestrator
# -------------------------------------------
def classify_jobs_ai(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """
    Orchestrates job classification by routing jobs to specialized AI classifiers
    based on their tags.
    """
    # Validate worker is reachable
    if not validate_worker_connection():
        print("⚠️  Skipping AI classification - worker unavailable")
        return df
    
    df = df.copy()

    # Prepare columns for classification results
    df["job_category"] = "Other"
    df["seniority"] = ""
    df["skills"] = ""  # Store as JSON string
    df["summary"] = ""
    df["matched_by"] = ""  # Track which tag matched
    df["confidence"] = 0.0  # Confidence score

    # Ensure required fields exist and are clean
    df["title"] = df["title"].fillna("")
    df["description_trunc"] = df["description"].fillna("").apply(truncate_description)
    df["tags"] = df["tags"].apply(lambda x: x if isinstance(x, list) else [])

    total_jobs = len(df)
    if verbose:
        print(f"\nClassifying {total_jobs} jobs using specialized AI classifiers...")
        print("="*60)

    # Iterator with progress bar
    iterator = tqdm(df.iterrows(), total=total_jobs, desc="Processing") if verbose else df.iterrows()

    for index, row in iterator:
        # Skip jobs with no tags
        if not row["tags"]:
            continue
        
        classified = False
        job_payload = {
            "title": row["title"],
            "description": row["description_trunc"]
        }
        
        # Try each tag until we get a match
        for tag in row["tags"]:
            if tag in TAG_TO_CLASSIFIER_MAP:
                classifier_info = TAG_TO_CLASSIFIER_MAP[tag]
                endpoint = classifier_info["endpoint"]
                
                # Call the specialized classifier
                result = call_classifier(endpoint, job_payload)

                # If the classifier confirms a match, update and stop
                if result.get("is_match"):
                    df.at[index, "job_category"] = classifier_info["category"]
                    df.at[index, "seniority"] = result.get("seniority", "")
                    df.at[index, "skills"] = json.dumps(result.get("skills", []))
                    df.at[index, "summary"] = result.get("summary", "")
                    df.at[index, "matched_by"] = tag
                    df.at[index, "confidence"] = result.get("confidence", 1.0)
                    
                    classified = True
                    break  # First match wins
    
    if verbose:
        print("="*60)
        print("\nClassification Summary:")
        print(df["job_category"].value_counts().to_string())
        print(f"\nTotal classified: {(df['job_category'] != 'Other').sum()}/{total_jobs}")

    return df