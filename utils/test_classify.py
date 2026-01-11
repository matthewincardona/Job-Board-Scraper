import pandas as pd
from utils.classifier_ai_pipeline import classify_jobs_ai

df = pd.read_csv("./jobs/test_jobs.csv")
df["company"] = ""
df["date_posted"] = ""

print(classify_jobs_ai(df))
