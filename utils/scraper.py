import pandas as pd
from jobspy import scrape_jobs
from datetime import datetime
import time

QUERIES = [
    'product designer',
    'ux designer',
    'ui designer',
    'interaction designer',
    'design intern',
    'ux intern',
    'product design intern',
]

SITES = ["linkedin", "indeed"]

def scrape_all_jobs():
    all_jobs = []
    
    for site in SITES:
        for q in QUERIES:
            try:
                print(f"\n[{site.upper()}] Scraping: '{q}'...", end=" ")
                
                jobs = scrape_jobs(
                    site_name=[site],
                    search_term=q,  # No quotes, no negatives
                    location="New York, NY",  # Full name
                    country_indeed='USA',
                    distance=50,
                    results_wanted=250,  # Increased
                    hours_old=720,
                    linkedin_fetch_description=True if site == "linkedin" else False,
                )
                
                count = len(jobs) if jobs is not None and not jobs.empty else 0
                print(f"✓ {count} jobs")
                
                if jobs is not None and not jobs.empty:
                    jobs['scraped_at'] = datetime.now().isoformat()
                    jobs['source_query'] = q
                    all_jobs.append(jobs)
                
                time.sleep(2)  # Rate limiting protection
                    
            except Exception as e:
                print(f"✗ Error: {e}")
                continue
    
    if not all_jobs:
        return pd.DataFrame()
    
    df = pd.concat(all_jobs, ignore_index=True)
    
    # Deduplicate by URL
    if 'job_url' in df.columns:
        before = len(df)
        df.drop_duplicates(subset=['job_url'], keep='first', inplace=True)
        print(f"\nDeduped: {before} → {len(df)}")
    
    return df