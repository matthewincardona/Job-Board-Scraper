import csv
import pandas as pd
from utils.scraper import scrape_all_jobs
from utils.markdown_cleaner import clean_markdown
from utils.classifier import classify_jobs
from utils.upload_jobs import upload_jobs_from_csv

def main():
    print("Starting scrape...")

    # Step 1 — Scrape
    scraped = scrape_all_jobs()
    print(f"Scraped: {len(scraped)} jobs")

    scraped.to_csv("./jobs/raw_jobs.csv", quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)

    # Step 2 — Clean
    print("Cleaning markdown...")
    scraped["description"] = scraped["description"].fillna("").apply(clean_markdown)

    # Step 3 — Classify
    classified = classify_jobs(scraped)

    # Step 4 — Deduplicate
    before = len(classified)
    classified.drop_duplicates(subset=["id"], inplace=True)
    after = len(classified)

    print(f"Deduped: {before} → {after}")

    # Save final dataset
    classified.to_csv("./jobs/classified_jobs.csv", index=False)
    print("Saved classified_jobs.csv")

    # Step 5 — Upload to Supabase
    print("Uploading to Supabase...")
    upload_jobs_from_csv("classified_jobs.csv")
    print("Upload complete.\n")

    # Summary
    ux = classified[classified.ux_category == "ux_designer"]
    interns = ux[ux.seniority == "intern"]
    entry = ux[ux.seniority == "entry"]

    print("\n------ Summary ------")
    print(f"UX roles: {len(ux)}")
    print(f"Entry-level: {len(entry)}")
    print(f"Internships: {len(interns)}")
    print("---------------------")


if __name__ == "__main__":
    main()
