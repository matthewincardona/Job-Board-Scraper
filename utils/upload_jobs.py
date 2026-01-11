import os
import csv
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime
from utils.markdown_cleaner import clean_markdown

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)


def safe_json_load(value):
    """
    Convert a CSV string like "{...}" into a Python dict.
    Returns {} if parsing fails.
    """
    if not value:
        return {}
    try:
        return json.loads(value)
    except:
        return {}


def transform_row(row):
    # -------------------
    # Parse date_posted
    # -------------------
    posted_at = None

    raw_date = row.get("date_posted")
    if raw_date:
        try:
            posted_at = datetime.fromisoformat(raw_date)
        except:
            try:
                posted_at = datetime.strptime(raw_date, "%Y-%m-%d")
            except:
                posted_at = None

    if not posted_at:
        posted_at = datetime.utcnow()

    posted_at_str = posted_at.isoformat() + "Z"

    # -------------------
    # Clean markdown
    # -------------------
    description = clean_markdown(row["description"])

    # -------------------
    # Convert scores (JSON strings → dict)
    # -------------------
    role_scores = safe_json_load(row.get("role_scores"))
    seniority_scores = safe_json_load(row.get("seniority_scores"))

    # -------------------
    # Return clean dict
    # -------------------
    return {
        "id": row["id"],
        "title": row["title"],
        "company_name": row["company"],
        "location": row["location"],
        "description_md": description,
        "job_url": row.get("job_url") or None,
        "job_url_direct": row.get("job_url_direct") or None,

        # NEW JSON score fields (jsonb in Supabase)
        "role_scores": role_scores,
        "seniority_scores": seniority_scores,

        # Shortcut string fields
        "ux_category": row.get("ux_category") or None,
        "seniority": row.get("seniority") or None,

        "date_posted": posted_at_str,
    }


def upload_jobs_from_csv(csv_path):
    with open(csv_path, encoding="utf8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            transformed = transform_row(row)
            supabase.table("jobs").upsert(transformed).execute()

    return True
