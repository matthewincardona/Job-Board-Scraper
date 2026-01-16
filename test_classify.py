import pandas as pd
from utils.classifier_ai_pipeline import classify_jobs_ai
from utils.upload_jobs import upload_jobs_from_csv
import sys
import os

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

# --- Test AI Classification ---
print("--- Testing AI Classification ---")
df = pd.read_csv("./jobs/test_jobs.csv")
classified = classify_jobs_ai(df, verbose=False)
print("✓ Classification complete. Results:")
print(classified[["title", "role_scores", "seniority_scores", "skills", "summary"]])

# --- Optional: Test Supabase Upload ---
if '--test-upload' in sys.argv:
    print("\n--- Testing Supabase Upload ---")
    
    # Save classified data to a temporary CSV for upload
    temp_csv_path = "./jobs/temp_upload_test.csv"
    classified.to_csv(temp_csv_path, index=False)
    
    try:
        print(f"Attempting to upload data from {temp_csv_path} to Supabase...")
        upload_jobs_from_csv(temp_csv_path)
        print("✓ Supabase upload function executed successfully.")
        print("Please check your 'jobs' table in Supabase to verify the records were added.")
    except Exception as e:
        print(f"✗ Supabase upload function failed: {e}")
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)
            print(f"✓ Cleaned up temporary file: {temp_csv_path}")