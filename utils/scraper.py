import pandas as pd
from jobspy import scrape_jobs
from datetime import datetime
import time

# ---------------------------------------
# Role-based Search Queries
# ---------------------------------------

UX_PRODUCT_QUERY = "product designer OR ux designer OR ui designer OR interaction designer OR visual designer"
FRONTEND_QUERY = "frontend developer OR ui developer OR ux engineer OR ui engineer OR web developer OR software engineer (javascript OR typescript OR react OR nodejs OR node OR html)"
CREATIVE_QUERY = "graphic design OR motion design OR web designer"

# This reduces ~15 queries down to 3 but still covers the intended roles
QUERIES = [
    UX_PRODUCT_QUERY,
    FRONTEND_QUERY,
    CREATIVE_QUERY,
]

# Map queries to tags for the specialized-classifier model
QUERY_TO_TAG_MAP = {
    UX_PRODUCT_QUERY: "possible_ux_product",
    FRONTEND_QUERY: "possible_frontend",
    CREATIVE_QUERY: "possible_creative",
}

# ---------------------------------------
# Other Search Parameters
# ---------------------------------------

LOCATIONS = [
    "New York, NY", "Seattle, WA", "San Francisco, CA", "San Jose, CA",
    "Austin, TX", "Boston, MA", "Los Angeles, CA", "Chicago, IL",
    "Denver, CO", "Redmond, WA"
]

SITES = ["linkedin", "indeed"]
HOURS_OLD = 720  # 30 days
RESULTS_WANTED = 250

# ---------------------------------------
# Main Scraper Function
# ---------------------------------------

def scrape_all_jobs():
    """
    Scrapes jobs from multiple sites, locations, and queries, tagging each job
    based on the source query.
    """
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
                        results_wanted=RESULTS_WANTED,
                        hours_old=HOURS_OLD,
                        linkedin_fetch_description=(site == "linkedin"),
                    )

                    count = len(jobs) if jobs is not None and not jobs.empty else 0
                    print(f"✓ {count} jobs")

                    if jobs is not None and not jobs.empty:
                        # Add metadata and tags
                        jobs["scraped_at"] = datetime.now().isoformat()
                        jobs["source_query"] = q
                        jobs["source_location"] = location
                        
                        # The core change: add a tag for the specialized classifier
                        tag = QUERY_TO_TAG_MAP.get(q)
                        if tag:
                            jobs["tags"] = [[tag] for _ in range(len(jobs))]
                        else:
                            jobs["tags"] = [[] for _ in range(len(jobs))]

                        all_jobs.append(jobs)

                    time.sleep(2)

                except Exception as e:
                    print(f"✗ Error: {e}")
                    continue

    if not all_jobs:
        return pd.DataFrame()

    # Combine all scraped jobs into a single dataframe
    df = pd.concat(all_jobs, ignore_index=True)

    # Alias 'title' to 'job_title' if needed for consistency
    if "job_title" not in df.columns and "title" in df.columns:
        df["job_title"] = df["title"]

    # Use job_url as the reliable unique identifier for deduplication
    if "job_url" in df.columns:
        df.drop_duplicates(subset=["job_url"], keep="first", inplace=True)
        # Set the 'id' column to the job_url
        df["id"] = df["job_url"]
    else:
        print("⚠️ Warning: 'job_url' not found. Cannot set 'id' or deduplicate effectively.")
        # As a fallback, create a temporary ID, but this is less reliable
        df['id'] = [hash(str(x)) for x in zip(df['job_title'], df['company_name'], df['location'])]


    print(f"\n✓ Total unique jobs scraped: {len(df)}")
    return df
