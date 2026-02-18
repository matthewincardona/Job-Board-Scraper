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


def get_existing_job_ids():
    """Fetches all job IDs from the Supabase table."""
    try:
        response = supabase.table("jobs").select("id").execute()
        return [job["id"] for job in response.data]
    except Exception as e:
        print(f"Error fetching existing job IDs: {e}")
        return []


def safe_json_load_dict(value):
    """
    Convert a CSV string like "{...}" into a Python dict.
    Returns {} if parsing fails.
    """
    if not value:
        return {}
    try:
        data = json.loads(value)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def safe_json_load_list(value):
    """
    Convert a CSV string like "[...]" into a Python list.
    Returns [] if parsing fails.
    """
    if not value:
        return []
    try:
        data = json.loads(value)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def transform_row(row, classified=True):
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

    base_job = {
        "id": row["id"],
        "title": row["title"],
        "company_name": row["company"],
        "company_logo": row["company_logo"],
        "location": row["location"],
        "description_md": description,
        "job_url": row.get("job_url") or None,
        "job_url_direct": row.get("job_url_direct") or None,
        "date_posted": posted_at_str,
    }

    if not classified:
        return base_job

    # -------------------
    # Convert scores and skills (JSON strings → dict/list)
    # -------------------
    role_scores = safe_json_load_dict(row.get("role_scores"))
    seniority_scores = safe_json_load_dict(row.get("seniority_scores"))
    skills = safe_json_load_list(row.get("skills"))

    # -------------------
    # Return clean dict
    # -------------------
    classified_job = {
        **base_job,
        "role_scores": role_scores,
        "seniority_scores": seniority_scores,
        "skills": skills,
        "summary": row.get("summary"),
    }
    return classified_job


def upload_jobs_from_csv(csv_path):
    with open(csv_path, encoding="utf8", newline="") as f:
        reader = csv.DictReader(f)
        records = [transform_row(row) for row in reader]

    if records:
        supabase.table("jobs").upsert(records).execute()

    return True


def upload_unclassified_jobs_df(jobs_df):
    """Upserts a DataFrame of unclassified jobs."""
    records = []
    for index, row in jobs_df.iterrows():
        transformed = transform_row(row.to_dict(), classified=False)
        records.append(transformed)

    if records:
        supabase.table("jobs").upsert(records).execute()

    return True