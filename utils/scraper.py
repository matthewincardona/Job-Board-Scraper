import pandas as pd
from jobspy import scrape_jobs
from datetime import datetime
import time
import hashlib

QUERIES = [
    'product designer',
    'ux designer',
    'interaction designer',
    'visual designer',
    'frontend developer',
    'software engineer (javascript OR typescript OR react OR nodejs OR node OR html)',
    'full stack',
    'ux engineer',
    'ui developer',
    'mobile developer',
    'graphic designer',
    'illustrator',
    'web designer'
]

# Major tech hubs
LOCATIONS = [
    "New York, NY",
    "Seattle, WA",
    "San Francisco, CA",
    "San Jose, CA",
    "Austin, TX",
    "Boston, MA",
    "Los Angeles, CA",
    "Chicago, IL",
    "Denver, CO",
    "Redmond, WA"
]

SITES = ["linkedin", "indeed"]

def normalize(x):
    """Safe normalize function for dedup fields."""
    if pd.isna(x):
        return ""
    return str(x).strip().lower()

def make_unique_id(row):
    title = normalize(row.get("job_title", ""))
    company = normalize(row.get("company_name", ""))
    location = normalize(row.get("location", ""))

    raw = f"{title}|{company}|{location}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def scrape_all_jobs():
    all_jobs = []
    
    for site in SITES:
        for location in LOCATIONS:
            for q in QUERIES:
                try:
                    print(f"\n[{site.upper()}] {location} : '{q}'...", end=" ")

                    jobs = scrape_jobs(
                        site_name=[site],
                        search_term=q,
                        location=location,
                        country_indeed="USA",
                        distance=50,
                        results_wanted=250,
                        hours_old=720,
                        linkedin_fetch_description=True if site == "linkedin" else False,
                    )

                    count = len(jobs) if jobs is not None and not jobs.empty else 0
                    print(f"✓ {count} jobs")

                    if jobs is not None and not jobs.empty:
                        jobs["scraped_at"] = datetime.now().isoformat()
                        jobs["source_query"] = q
                        jobs["source_location"] = location
                        all_jobs.append(jobs)

                    time.sleep(2) # Rate limiting protection

                except Exception as e:
                    print(f"✗ Error: {e}")
                    continue
            
    if not all_jobs:
        return pd.DataFrame()
    
    df = pd.concat(all_jobs, ignore_index=True)

    # -------------------------------------------
    # CREATE UNIQUE ID for deduping
    # -------------------------------------------
    # Some jobspy datasets use `job_title`, some use `title`.
    if "job_title" not in df.columns and "title" in df.columns:
        df["job_title"] = df["title"]

    df["unique_id"] = df.apply(make_unique_id, axis=1)

    before = len(df)
    df.drop_duplicates(subset=["unique_id"], keep="first", inplace=True)
    print(f"\nDeduped: {before} → {len(df)} by unique_id (title + company + location)")

    return df

