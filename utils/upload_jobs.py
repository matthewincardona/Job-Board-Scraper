import os
import csv
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime
from utils.markdown_cleaner import clean_markdown

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def transform_row(row):
    # Try to parse date_posted
    posted_at = None
    if row["date_posted"]:
        try:
            posted_at = datetime.fromisoformat(row["date_posted"])
        except:
            try:
                posted_at = datetime.strptime(row["date_posted"], "%Y-%m-%d")
            except:
                posted_at = None

    # Fallback if missing
    if not posted_at:
        posted_at = datetime.utcnow()  # <-- always fill in a valid timestamp

    posted_at_str = posted_at.isoformat() + "Z"  # ISO 8601 with UTC

    # Clean markdown for rendering in UI
    description = clean_markdown(row["description"])

    return {
        "id": row["id"],
        "title": row["title"],
        "company_name": row["company"],
        "location": row["location"],
        "description_md": description,
        "job_url": row["job_url"] or None,
        "job_url_direct": row["job_url_direct"] or None,
        "ux_score": float(row["ux_score"]) if row.get("ux_score") else 0,
        "ux_category": row["ux_category"] or None,
        "seniority": row["seniority"] or None,
        "date_posted": posted_at_str,    
    }

def upload_jobs_from_csv(csv_path):
    with open(csv_path, encoding="utf8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            transformed = transform_row(row)
            supabase.table("jobs").upsert(transformed).execute()

    return True  # so main.py can know it's done
