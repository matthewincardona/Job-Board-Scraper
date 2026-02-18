import csv
import sys
import pandas as pd
from datetime import datetime
from utils.scraper import scrape_all_jobs
from utils.classifier import classify_and_filter_jobs
from utils.markdown_cleaner import clean_markdown
from utils.classifier_ai_pipeline import classify_jobs_ai
from utils.upload_jobs import upload_jobs_from_csv, get_existing_job_ids, upload_unclassified_jobs_df


def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    skip_scrape = len(sys.argv) > 1 and sys.argv[1] == "skip"

    # -------------------------
    # Step 1 — Scrape or Load Existing
    # -------------------------
    if skip_scrape:
        print("Skipping scrape. Loading most recent raw_jobs file...")

        import glob
        files = sorted(glob.glob("./jobs/raw_jobs_*.csv"))
        if not files:
            print("✗ No raw_jobs_*.csv found. Cannot skip scrape.")
            return

        last_raw = files[-1]
        scraped = pd.read_csv(last_raw)
        print(f"✓ Loaded {len(scraped)} jobs from {last_raw}")

    else:
        try:
            print("Starting scrape...")
            scraped = scrape_all_jobs()

            if scraped.empty:
                print("⚠️  No jobs scraped. Exiting.")
                return

            print(f"✓ Scraped: {len(scraped)} jobs")

            raw_path = f"./jobs/raw_jobs_{timestamp}.csv"
            scraped.to_csv(
                raw_path,
                quoting=csv.QUOTE_NONNUMERIC,
                escapechar="\\",
                index=False,
            )
            print(f"✓ Saved raw data to {raw_path}")

        except Exception as e:
            print(f"✗ Scraping failed: {e}")
            return

    # -------------------------
    # Step 2 — Separate new and existing jobs
    # -------------------------
    try:
        print("\nSeparating new and existing jobs...")
        existing_job_ids = get_existing_job_ids()
        
        new_jobs = scraped[~scraped['id'].isin(existing_job_ids)]
        existing_jobs = scraped[scraped['id'].isin(existing_job_ids)]
        
        print(f"✓ Found {len(new_jobs)} new jobs and {len(existing_jobs)} existing jobs.")

    except Exception as e:
        print(f"✗ Failed to separate jobs: {e}")
        return

    # -------------------------
    # Step 3 — Update existing jobs
    # -------------------------
    if not existing_jobs.empty:
        try:
            print("\nUpdating existing jobs in Supabase...")
            upload_unclassified_jobs_df(existing_jobs)
            print(f"✓ Updated {len(existing_jobs)} existing jobs.")
        except Exception as e:
            print(f"✗ Failed to update existing jobs: {e}")
            # Non-fatal, we can continue with the new jobs
    
    # -------------------------
    # Step 4 — Filter by title
    # -------------------------
    if new_jobs.empty:
        print("\nNo new jobs to process. Exiting.")
        return
        
    try:
        print("\nFiltering new jobs by title...")
        classified = classify_and_filter_jobs(new_jobs)
    except Exception as e:
        print(f"✗ Filtering failed: {e}")
        return

    # -------------------------
    # Step 5 — Clean Markdown
    # -------------------------
    try:
        print("\nCleaning markdown...")
        classified["description"] = classified["description"].fillna("").apply(clean_markdown)
        print(f"✓ Cleaned {len(classified)} descriptions")
    except Exception as e:
        print(f"✗ Cleaning failed: {e}")
        return

    # -------------------------
    # Step 6 — Classify using AI Worker
    # -------------------------
    try:
        print("\nClassifying jobs with AI Worker...")
        classified = classify_jobs_ai(classified, batch_size=10)

        print(f"✓ Classified {len(classified)} jobs")

    except Exception as e:
        print(f"✗ Classification failed: {e}")
        return

    # -------------------------
    # Step 7 — Deduplicate
    # -------------------------
    try:
        print("\nDeduplicating...")
        before = len(classified)
        classified.drop_duplicates(subset=["id"], inplace=True)
        after = len(classified)
        print(f"✓ Deduped: {before} → {after} ({before - after} duplicates removed)")

        classified_path = f"./jobs/classified_jobs_{timestamp}.csv"
        classified.to_csv(classified_path, index=False)
        classified.to_csv("./jobs/classified_jobs.csv", index=False)
        print(f"✓ Saved classified data to {classified_path}")

    except Exception as e:
        print(f"✗ Deduplication/saving failed: {e}")
        return

    # -------------------------
    # Step 8 — Upload to Supabase
    # -------------------------
    try:
        print("\nUploading to Supabase...")
        upload_jobs_from_csv("./jobs/classified_jobs.csv")
        print("✓ Upload complete")

    except Exception as e:
        print(f"✗ Upload failed: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)