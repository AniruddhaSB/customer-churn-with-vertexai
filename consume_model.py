import pandas as pd
import os
import joblib
import pickle
from google.cloud import storage
from preprocess_data import preprocess_data

def predict_using_pretrained_model(
        project_id: str,
        bucket_name: str,
        prod_model_folder_path: str,
        processed_data_folder_path: str,
        userInput_df: pd.DataFrame):
    
    """Function to make predictions using a pre-trained model."""
    
    print("--- Configuration ---")
    print(f"Project ID: {project_id}")
    print(f"Bucket Name: {bucket_name}")
    print(f"Prod Model Folder Path: {prod_model_folder_path}")
    print(f"Processed Data Folder Path: {processed_data_folder_path}")
    print("---------------------")

    try:
        # Load the pre-trained model from GCS
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.bucket(bucket_name)

        blobs = bucket.list_blobs(prefix=prod_model_folder_path)
        model_blob_name = [blob.name for blob in blobs if blob.name.endswith('.joblib')][0]
        print(f"model_blob_name: {model_blob_name}")

        model_blob = bucket.blob(model_blob_name)

        print("Downloading model file...")
        local_file_path = "modelFile.joblib"

        with open(local_file_path, "wb") as file:
            model_blob.download_to_file(file)

        model = joblib.load(local_file_path)
        print("Model loaded successfully for prediction.")

        #load scaler and encoder
        scalar_path = f"{processed_data_folder_path}scaler.pkl"
        encoder_path = f"{processed_data_folder_path}encoder.pkl"
        print(f"Loading scaler from {scalar_path}")
        print(f"Loading encoder from {encoder_path}")

        scalar_blob = bucket.blob(scalar_path)
        local_file_path = "scalerFile.pkl"

        with open(local_file_path, "wb") as file:
            scalar_blob.download_to_file(file)

        with open(local_file_path, "rb") as file:
            preloaded_scaler = pickle.load(file)

        print("scaler loaded successfully for prediction.")

        encoder_blob = bucket.blob(encoder_path)
        local_file_path = "encoderFile.pkl"

        with open(local_file_path, "wb") as file:
            encoder_blob.download_to_file(file)

        with open(local_file_path, "rb") as file:
            preloaded_encoder = pickle.load(file)

        print("encoder loaded successfully for prediction.")

        print(f"user input data:{userInput_df}")
        #preprocess user input
        processed_input, scaler1,encoder1 = preprocess_data(
            df=userInput_df, 
            input_scalar=preloaded_scaler, 
            input_encoder=preloaded_encoder
        )
        processed_input = processed_input.drop('Churn', axis=1)
        print(f"Processed user input data:{processed_input}")

        # Make predictions
        predictions = model.predict(processed_input)
        print(f"Predictions made successfully. Predictions: {predictions}")
        return userInput_df, processed_input, predictions
    except Exception as e:
        print(f"ERROR: Failed to make predictions. Details: {e}")
        return pd.DataFrame(), pd.DataFrame(), None
    