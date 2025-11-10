import subprocess
import os
import sys
import pandas as pd
from google.cloud import storage

from dotenv import load_dotenv

def load_data(
        project_id: str,
        bucket_name: str,
        raw_data_folder_path: str,
    ) -> pd.DataFrame:
    """Function to load data from GCS bucket."""
    if not all([project_id, bucket_name, raw_data_folder_path]):
        print("Error: Missing one or more required environment variables.")
        return pd.DataFrame()

    print("--- Configuration ---")
    print(f"Project ID: {project_id}")
    print(f"Bucket Name: {bucket_name}")
    print(f"Raw Data Folder Path: {raw_data_folder_path}")
    print("---------------------")

    #1. Read all the CSV files from the specified GCS folder
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=raw_data_folder_path)
    csv_files = [blob.name for blob in blobs if blob.name.endswith('.csv')]
    print(f"Found {len(csv_files)} CSV files in the specified GCS folder.")

    data_frames = []
    for file in csv_files:
        df = pd.read_csv(f"gs://{bucket_name}/{file}")
        print(f"Loaded {len(df)} records from {file}.")
        data_frames.append(df)

    combined_data = pd.concat(data_frames, ignore_index=True)
    print(f"Loaded {len(combined_data)} records from {len(csv_files)} files.")

    return combined_data 


# --- Example Usage ---
if __name__ == "__main__":
    # Load variables from the .env file in the current directory
    load_dotenv()

    # Retrieve variables, falling back to provided defaults if not found in .env
    PROJECT_ID = os.getenv("PROJECT_ID", "nimble-octagon-253816")
    BUCKET_NAME = os.getenv("BUCKET_NAME", "customer-churn-demo")
    RAW_DATA_FOLDER_PATH = os.getenv("RAW_DATA_FOLDER_PATH", "data/raw/")
    
    raw_data = load_data(
        project_id=PROJECT_ID,
        bucket_name=BUCKET_NAME,
        raw_data_folder_path=RAW_DATA_FOLDER_PATH
    )

    if raw_data.empty is True:
        print("\nNo data loaded.")
    else:
        print(f"Data loaded successfully with {raw_data.shape[0]} records.")