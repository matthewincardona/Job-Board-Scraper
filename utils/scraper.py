import pandas as pd
from jobspy import scrape_jobs

QUERIES = [
    '"ux designer" OR "ux ui designer" OR "ui ux designer"',
    '"ui designer" OR "user interface designer"',
    '"product designer" OR "digital product designer"',
    '"interaction designer" OR "experience designer" OR "visual designer"',
    '"user experience" OR "ux research" OR "ux"',
    '"design intern" OR "ux intern" OR "product design intern" OR "junior designer" OR "associate designer"',
]

NEGATIVES = '-senior -sr -staff -lead -principal -manager -director -head -vp'


def scrape_all_jobs():
    all_jobs = []

    for q in QUERIES:
        print(f"\nScraping: {q}")
        jobs = scrape_jobs(
            site_name=["linkedin"],
            search_term=f'({q}) {NEGATIVES}',
            location="NY, NY",
            distance=100,
            results_wanted=80,
            hours_old=731,
            linkedin_fetch_description=True,
        )
        print(f"Found: {len(jobs)}")
        all_jobs.append(jobs)

    if not all_jobs:
        return pd.DataFrame()

    df = pd.concat(all_jobs, ignore_index=True)
    return df
