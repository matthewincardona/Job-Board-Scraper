import csv
import sys
import pandas as pd
from datetime import datetime
import ast

from utils.scraper import scrape_all_jobs
from utils.markdown_cleaner import clean_markdown
from utils.classifier_ai_pipeline import classify_jobs_ai
from utils.upload_jobs import upload_jobs_from_csv

def agg_tags(tags_series):
    """Helper to aggregate tags from multiple job posts into a unique set."""
    all_tags = set()
    for tags_list in tags_series:
        # The tags can be a string representation of a list, so we evaluate it
        if isinstance(tags_list, str):
            try:
                tags_list = ast.literal_eval(tags_list)
            except (ValueError, SyntaxError):
                tags_list = []
        if isinstance(tags_list, list):
            for tag in tags_list:
                all_tags.add(tag)
    return list(all_tags)


def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    skip_scrape = len(sys.argv) > 1 and sys.argv[1] == "skip"

    # -------------------------
    # Step 1: Scrape or Load
    # -------------------------
    if skip_scrape:
        print("Skipping scrape. Loading most recent raw_jobs file...")
        import glob
        files = sorted(glob.glob("./jobs/raw_jobs_*.csv"))
        if not files:
            print("✗ No raw_jobs_*.csv found. Cannot skip scrape.")
            return
        
        raw_jobs_path = files[-1]
        jobs_df = pd.read_csv(raw_jobs_path)
        print(f"✓ Loaded {len(jobs_df)} jobs from {raw_jobs_path}")
    else:
        print("Starting scrape...")
        jobs_df = scrape_all_jobs()
        if jobs_df.empty:
            print("⚠️ No jobs scraped. Exiting.")
            return

        print(f"✓ Scraped {len(jobs_df)} total job posts.")
        raw_jobs_path = f"./jobs/raw_jobs_{timestamp}.csv"
        jobs_df.to_csv(raw_jobs_path, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)
        print(f"✓ Saved raw data to {raw_jobs_path}")

    # -------------------------
    # Step 2: Deduplicate & Merge Tags
    # -------------------------
    print("\nDeduplicating jobs and merging tags...")
    initial_count = len(jobs_df)
    
    # Group by 'id' and aggregate. We keep the first non-null value for each column,
    # and we specifically merge the 'tags' column.
    agg_funcs = {col: 'first' for col in jobs_df.columns if col not in ['id', 'tags']}
    agg_funcs['tags'] = agg_tags
    
    deduped_df = jobs_df.groupby('id').agg(agg_funcs).reset_index()
    
    final_count = len(deduped_df)
    print(f"✓ Deduped: {initial_count} posts -> {final_count} unique jobs ({initial_count - final_count} duplicates removed).")

    # -------------------------
    # Step 3: Clean Markdown
    # -------------------------
    print("\nCleaning markdown from descriptions...")
    deduped_df["description"] = deduped_df["description"].fillna("").apply(clean_markdown)
    print(f"✓ Cleaned {len(deduped_df)} descriptions.")

    # -------------------------
    # Step 4: Classify via Specialized AI
    # -------------------------
    print("\nClassifying jobs with specialized AI classifiers...")
    classified_df = classify_jobs_ai(deduped_df)
    print(f"✓ AI classification complete.")

    # -------------------------
    # Step 5: Filter Unclassified & Save
    # -------------------------
    print("\nFiltering out jobs classified as 'Other'...")
    initial_classified_count = len(classified_df)
    
    # The 'job_category' is set by the classifier; we discard what doesn't fit.
    final_df = classified_df[classified_df['job_category'] != 'Other'].copy()
    
    final_count = len(final_df)
    print(f"✓ Filtering complete: {initial_classified_count} -> {final_count} jobs ({initial_classified_count - final_count} 'Other' jobs removed).")

    if final_df.empty:
        print("⚠️ No jobs passed classification. Nothing to upload.")
        return

    # Save the final, classified jobs
    classified_path = f"./jobs/classified_jobs_{timestamp}.csv"
    final_df.to_csv(classified_path, index=False, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\")
    # Also save a consistent path for the upload step
    final_df.to_csv("./jobs/classified_jobs.csv", index=False, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\")
    print(f"✓ Saved {len(final_df)} classified jobs to {classified_path}")

    # -------------------------
    # Step 6: Upload to Supabase
    # -------------------------
    print("\nUploading to Supabase...")
    try:
        upload_jobs_from_csv("./jobs/classified_jobs.csv")
        print("✓ Upload complete.")
    except Exception as e:
        print(f"✗ Upload failed: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Pipeline interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
