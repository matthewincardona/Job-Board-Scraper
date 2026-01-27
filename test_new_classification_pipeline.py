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
print("--- Testing New AI Classification Pipeline ---")
df = pd.read_csv("./jobs/new_test_jobs.csv")

# The 'tags' column is read as a string, so we need to convert it to a list
import ast
df['tags'] = df['tags'].apply(ast.literal_eval)

classified = classify_jobs_ai(df, verbose=True)
print("\n--- Classification Results ---")
print(classified[["title", "tags", "job_category", "seniority", "skills", "summary"]])

# --- Optional: Test Supabase Upload ---
if '--test-upload' in sys.argv:
    print("\n--- Testing Supabase Upload ---")
    
    # Save classified data to a temporary CSV for upload
    temp_csv_path = "./jobs/temp_upload_test.csv"
    classified.to_csv(temp_csv_path, index=False)
    
    try:
        print(f"Attempting to upload data from {temp_csv_path} to Supabase...")
        # I'll need to create a dummy file for the upload to work
        # in a test environment without a real Supabase instance.
        # For this test, I will just call the function.
        # In a real scenario, this would require mocking.
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
