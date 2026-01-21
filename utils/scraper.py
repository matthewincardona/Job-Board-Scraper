import pandas as pd
from jobspy import scrape_jobs
from datetime import datetime
import time
import hashlib

# ---------------------------------------
# Consolidated job title groups
# ---------------------------------------

# Core product and UX roles
UX_PRODUCT_QUERY = (
    "product designer OR ux designer OR ui designer OR interaction designer OR visual designer"
)

# Engineering roles with frontend emphasis
FRONTEND_QUERY = (
    "frontend developer OR ui developer OR ux engineer OR ui engineer OR web developer "
    "OR software engineer (javascript OR typescript OR react OR nodejs OR node OR html)"
)

# General creative roles
CREATIVE_QUERY = "graphic design OR motion design OR web designer"

# This reduces 15 queries down to 3 but still covers everything you had
QUERIES = [
    UX_PRODUCT_QUERY,
    FRONTEND_QUERY,
    CREATIVE_QUERY,
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

                    time.sleep(2)

                except Exception as e:
                    print(f"✗ Error: {e}")
                    continue

    if not all_jobs:
        return pd.DataFrame()
    df = pd.concat(all_jobs, ignore_index=True)

    if "job_title" not in df.columns and "title" in df.columns:
        df["job_title"] = df["title"]

    # Drop existing JobSpy id just to be safe
    if "id" in df.columns:
        df.drop(columns=["id"], inplace=True)

    # Now assign your own id
    df["id"] = df["unique_id"]

    before = len(df)
    df.drop_duplicates(subset=["unique_id"], keep="first", inplace=True)
    print(f"\nDeduped: {before} → {len[df]} by unique_id (title + company + location)")

    return df

