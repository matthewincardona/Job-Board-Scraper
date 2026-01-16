# Job Board Scraper & AI Classifier

This project is a sophisticated pipeline for automatically scraping job boards, cleaning the data, classifying it using an AI model, and uploading the results to a Supabase database.

## Features

- **Multi-Source Scraping:** Scrapes job postings from various job boards using the `jobspy` library.
- **Data Cleaning:** Cleans and formats scraped job descriptions, converting Markdown to plain text.
- **AI-Powered Classification:** Utilizes a Cloudflare AI Worker (running a Llama-3.2-3B model) to classify jobs based on role, seniority, and required skills.
- **Deduplication:** Removes duplicate job postings to ensure data quality.
- **Automated Upload:** Uploads the final, classified job data to a Supabase table.

## Tech Stack

- **Backend:** Python
- **Data Manipulation:** pandas
- **Web Scraping:** jobspy
- **AI Model Hosting:** Cloudflare Workers
- **Database:** Supabase
- **Dependencies:** See `requirements.txt` for a full list of Python packages.

## Workflow Pipeline

The main script (`main.py`) orchestrates the following steps:

1.  **Scrape or Load:** It can either scrape new jobs or load the most recent raw job data from a CSV file in the `/jobs` directory.
2.  **Clean Markdown:** Job descriptions are cleaned by stripping Markdown formatting.
3.  **Classify with AI:** The cleaned data is sent in batches to the Cloudflare AI worker, which returns structured data including role scores, seniority scores, skills, and a summary.
4.  **Deduplicate:** The classified data is deduplicated based on job ID.
5.  **Save & Upload:** The final, cleaned, and classified data is saved to `jobs/classified_jobs.csv` and then uploaded to Supabase.

## Setup and Usage

### 1. Python Environment

It is recommended to use a virtual environment.

```bash
# Create and activate the virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Cloudflare AI Worker

This project requires a Cloudflare Worker to be running and accessible at `http://127.0.0.1:8787/`.

1.  Navigate to the `ai-classifier-worker/hello-ai` directory.
2.  Install the Node.js dependencies: `npm install`.
3.  Run the worker locally: `npx wrangler dev`.

See the `wrangler.toml` file for the worker's configuration.

### 3. Supabase

You will need a Supabase project set up, and the appropriate environment variables (URL and key) configured for the `upload_jobs.py` script to work.

### 4. Running the Pipeline

Once the virtual environment is active and the AI worker is running, you can execute the main script:

```bash
# Run the full pipeline (scrape, clean, classify, upload)
python main.py

# To skip the scraping step and use the latest raw_jobs CSV
python main.py skip
```

## Project Structure

```
.
├── ai-classifier-worker/  # Cloudflare worker for AI classification
│   └── hello-ai/
│       ├── src/index.ts   # The AI worker script
│       └── wrangler.toml  # Worker configuration
├── jobs/                  # Output directory for scraped and classified CSVs
├── utils/                 # Utility scripts
│   ├── scraper.py         # Job scraping logic
│   ├── markdown_cleaner.py # Markdown cleaning utility
│   ├── classifier_ai_pipeline.py # Handles communication with the AI worker
│   └── upload_jobs.py     # Logic for uploading data to Supabase
├── main.py                # Main script to run the entire pipeline
├── requirements.txt       # Python dependencies
└── README.md              # This file
```