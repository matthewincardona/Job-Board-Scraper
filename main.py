import csv
import sys
import pandas as pd
from datetime import datetime
from utils.scraper import scrape_all_jobs
from utils.markdown_cleaner import clean_markdown
from utils.classifier import classify_jobs
from utils.upload_jobs import upload_jobs_from_csv

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Step 1 — Scrape
        print("Starting scrape...")
        scraped = scrape_all_jobs()
        
        if scraped.empty:
            print("⚠️  No jobs scraped. Exiting.")
            return
        
        print(f"✓ Scraped: {len(scraped)} jobs")
        
        # Save raw immediately
        raw_path = f"./jobs/raw_jobs_{timestamp}.csv"
        scraped.to_csv(raw_path, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)
        print(f"✓ Saved raw data to {raw_path}")
        
    except Exception as e:
        print(f"✗ Scraping failed: {e}")
        return
    
    try:
        # Step 2 — Clean
        print("\nCleaning markdown...")
        scraped["description"] = scraped["description"].fillna("").apply(clean_markdown)
        print(f"✓ Cleaned {len(scraped)} descriptions")
        
    except Exception as e:
        print(f"✗ Cleaning failed: {e}")
        return
    
    try:
        # Step 3 — Classify
        print("\nClassifying jobs...")
        classified = classify_jobs(scraped)
        
        # Validate classification
        if "ux_category" not in classified.columns or "seniority" not in classified.columns:
            raise ValueError("Classification did not produce expected columns")
        
        print(f"✓ Classified {len(classified)} jobs")
        
    except Exception as e:
        print(f"✗ Classification failed: {e}")
        return
    
    try:
        # Step 4 — Deduplicate
        print("\nDeduplicating...")
        before = len(classified)
        classified.drop_duplicates(subset=["id"], inplace=True)
        after = len(classified)
        print(f"✓ Deduped: {before} → {after} ({before - after} duplicates removed)")
        
        # Save classified dataset
        classified_path = f"./jobs/classified_jobs_{timestamp}.csv"
        classified.to_csv(classified_path, index=False)
        
        # Also save to standard location for easy access
        classified.to_csv("./jobs/classified_jobs.csv", index=False)
        print(f"✓ Saved classified data to {classified_path}")
        
    except Exception as e:
        print(f"✗ Deduplication/saving failed: {e}")
        return
    
    # Step 5 — Upload to Supabase
    try:
        print("\nUploading to Supabase...")
        upload_result = upload_jobs_from_csv("./jobs/classified_jobs.csv")
        
        # Assuming upload_jobs_from_csv returns some result
        print("✓ Upload complete")
        
    except Exception as e:
        print(f"✗ Upload failed: {e}")
        print(f"⚠️  Data is saved locally at {classified_path}")
        # Don't return here - still show summary
    
    # Summary
    print("\n" + "="*40)
    print("PIPELINE SUMMARY")
    print("="*40)
    
    ux = classified[classified.ux_category == "ux_designer"]
    interns = ux[ux.seniority == "intern"]
    entry = ux[ux.seniority == "entry"]
    unknown = ux[ux.seniority == "unknown"]
    
    print(f"Total jobs processed: {len(classified)}")
    print(f"UX roles identified: {len(ux)} ({len(ux)/len(classified)*100:.1f}%)")
    print(f"  ├─ Internships: {len(interns)}")
    print(f"  ├─ Entry-level: {len(entry)}")
    print(f"  └─ Unknown level: {len(unknown)}")
    print("="*40)
    
    # Quality checks
    if len(ux) == 0:
        print("⚠️  WARNING: No UX jobs found. Check classifier logic.")
    
    if len(unknown) > len(entry) + len(interns):
        print("⚠️  WARNING: Many jobs with unknown seniority. Consider improving classifier.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)