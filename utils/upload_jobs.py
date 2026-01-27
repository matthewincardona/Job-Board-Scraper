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

def safe_json_load_list(value):
    """
    Convert a CSV string that looks like a list (e.g., "['skill1', 'skill2']")
    into a Python list. Returns an empty list if parsing fails.
    """
    if not value or not isinstance(value, str):
        return []
    try:
        # The string might be single-quoted from pandas, json loads needs double quotes
        value = value.replace("'", '"')
        data = json.loads(value)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, TypeError):
        return []

def transform_row(row):
    """
    Transforms a single CSV row into a dictionary suitable for Supabase upsert,
    aligning with the new tag-based classification schema.
    """
    # --- Date Handling ---
    posted_at = None
    raw_date = row.get("date_posted") or row.get("posted_at")
    if raw_date:
        try:
            # Handle ISO format with timezone
            if 'Z' in raw_date or '+' in raw_date:
                posted_at = datetime.fromisoformat(raw_date.replace('Z', '+00:00'))
            else:
                posted_at = datetime.fromisoformat(raw_date)
        except (ValueError, TypeError):
            try:
                posted_at = datetime.strptime(raw_date, "%Y-%m-%d")
            except (ValueError, TypeError):
                posted_at = None
    
    # Default to now if parsing fails
    if not posted_at:
        posted_at = datetime.utcnow()
    
    posted_at_str = posted_at.isoformat() + "Z"

    # --- Data Cleaning and Mapping ---
    return {
        "id": row.get("id"),
        "title": row.get("title") or row.get("job_title"),
        "company_name": row.get("company_name") or row.get("company"),
        "company_logo": row.get("company_logo_url") or row.get("company_logo"),
        "location": row.get("location"),
        "description_md": clean_markdown(row.get("description", "")),
        "job_url": row.get("job_url"),
        
        # New classification fields
        "job_category": row.get("job_category"),
        "seniority": row.get("seniority"),
        "skills": safe_json_load_list(row.get("skills")),
        "summary": row.get("summary"),
        
        "date_posted": posted_at_str,
        
        # Deprecated fields - explicitly set to null or empty
        "role_scores": {},
        "seniority_scores": {},
    }

def upload_jobs_from_csv(csv_path):
    """
    Reads a CSV file of classified jobs and uploads them to the Supabase 'jobs' table.
    """
    try:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            jobs_to_upload = [transform_row(row) for row in reader]

        if not jobs_to_upload:
            print("No jobs to upload.")
            return True

        print(f"Attempting to upsert {len(jobs_to_upload)} jobs...")
        # Upsert in batches (Supabase has limits, though they are high)
        # For simplicity, sending all at once, but for >1000s of rows, batching is better.
        response = supabase.table("jobs").upsert(jobs_to_upload).execute()
        
        # Basic error checking
        if hasattr(response, 'error') and response.error:
            print(f"✗ Supabase error: {response.error}")
            return False

        print(f"✓ Successfully upserted {len(jobs_to_upload)} jobs.")
        return True

    except FileNotFoundError:
        print(f"✗ Error: The file at {csv_path} was not found.")
        return False
    except Exception as e:
        print(f"✗ An unexpected error occurred during upload: {e}")
        return False
