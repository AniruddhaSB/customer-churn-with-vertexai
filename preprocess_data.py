import pandas as pd
import pickle
import io
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import LabelEncoder
from google.cloud import storage

def preprocess_data(
        df: pd.DataFrame,
        input_scalar: any = None,
        input_encoder: any = None
    ):
    """Function to preprocess data."""

    if df.empty is True:
        print("Error: Input DataFrame is empty.")
        return pd.DataFrame(), None, None
    
    print("--- Preprocessing Data ---")
    print(f"Input records: {len(df)}")

    df = df.dropna()
    print(f"Dropped missing values. Remaining records: {len(df)}")

    df = df.drop_duplicates()
    print(f"Dropped duplicate records. Remaining records: {len(df)}")

    df = df.drop(['CustomerID'], axis=1)
    print(f"Dropped CustomerID column. Remaining records: {len(df)}")

    print(df.head(5))

    # Feature Engineering:
    df['RecentlyActive'] = (df['Last Interaction'] < 5).astype(int)
    df['HighSupportUser'] = (df['Support Calls'] > 5).astype(int)

    numerical_cols = df.select_dtypes(include=['number']).columns
    numerical_cols = numerical_cols.drop('Churn')
    numerical_cols = numerical_cols.drop('RecentlyActive')
    numerical_cols = numerical_cols.drop('HighSupportUser')

    print(numerical_cols)
    if input_scalar is not None:
        print("Using provided scaler for normalization.")
        scaler = input_scalar
        scaled_data = scaler.transform(df[numerical_cols])
    else:
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(df[numerical_cols])

    # 3. Convert the resulting NumPy array back into a DataFrame, 
    #    using the original index and column names
    scaled_df = pd.DataFrame(
        scaled_data, 
        columns=numerical_cols, 
        index=df.index
    )

    df[numerical_cols] = scaled_df[numerical_cols]

    print(df.head(5))
    print(f"Normalized numerical columns. Remaining records: {len(df)}")

    categorical_cols = df.select_dtypes(include=['object']).columns
    print(categorical_cols)
    
    if input_encoder is not None:
        print("Using provided encoder for categorical encoding.")
        le = input_encoder
    else:
        le = LabelEncoder()

    for col in categorical_cols:
        # Apply Label Encoding to each categorical column
        df[col] = le.fit_transform(df[col])

    print(df.head(5))
    print(f"Encoded categorical columns. Remaining records: {len(df)}")

    print("--- Preprocessing Complete ---")

    return df, scaler,le

def save_processed_data(
        project_id: str,
        bucket_name: str,
        processed_data_folder_path: str,
        df: pd.DataFrame,
        file_name: str = "processed_data.csv"
    ):
    """Function to save processed data to a CSV file."""

    if df.empty is True:
        return False, "Error: Input DataFrame is empty. Cannot save."

    try:    
        output_path = f"gs://{bucket_name}/{processed_data_folder_path}{file_name}"
        blob_name = f"{processed_data_folder_path}{file_name}"
        client = storage.Client(project=project_id)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        if blob.exists():
            print(f"File already exists at {bucket_name}/{blob_name}. Deleting old file...")
            blob.delete()
            print("Old file deleted successfully.")
            
        df.to_csv(output_path, index=False)
        return True, f"Processed data saved to {output_path}"
    except Exception as e:
        return False, f"ERROR: Failed to save processed data to {output_path}. Details: {e}"
    

def save_scalar(
    project_id: str,
    bucket_name: str,
    processed_data_folder_path: str,
    scaler
):
    """Function to save scaler object to GCS."""

    file_name = "scaler.pkl"
    print(f"Saving scaler to gs://{bucket_name}/{processed_data_folder_path}{file_name}")
    
    try:
        client = storage.Client(project=project_id)
        bucket = client.bucket(bucket_name)
        blob_name = f"{processed_data_folder_path}{file_name}"
        blob = bucket.blob(blob_name)
        
        if blob.exists():
            print(f"File already exists at {bucket_name}/{blob_name}. Deleting old file...")
            blob.delete()
            print("Old file deleted successfully.")
        
        buffer = io.BytesIO()
        pickle.dump(scaler, buffer)
        buffer.seek(0)
        blob.upload_from_file(buffer, content_type='application/octet-stream')

        return True, f"SUCCESS: {file_name} saved to gs://{bucket_name}/{blob_name}"
    except Exception as e:
        return False, f"ERROR: Failed to save {file_name} to GCS. Details: {e}"

def save_encoder(
    project_id: str,
    bucket_name: str,
    processed_data_folder_path: str,
    encoder
):
    """Function to save scaler object to GCS."""

    file_name = "encoder.pkl"
    print(f"Saving encoder to gs://{bucket_name}/{processed_data_folder_path}{file_name}")
    
    try:
        client = storage.Client(project=project_id)
        bucket = client.bucket(bucket_name)
        blob_name = f"{processed_data_folder_path}{file_name}"
        blob = bucket.blob(blob_name)

        if blob.exists():
            print(f"File already exists at {bucket_name}/{blob_name}. Deleting old file...")
            blob.delete()
            print("Old file deleted successfully.")

        buffer = io.BytesIO()
        pickle.dump(encoder, buffer)
        buffer.seek(0)
        blob.upload_from_file(buffer, content_type='application/octet-stream')

        return True, f"SUCCESS: {file_name} saved to gs://{bucket_name}/{blob_name}"
    except Exception as e:
        return False, f"ERROR: Failed to save {file_name} to GCS. Details: {e}"