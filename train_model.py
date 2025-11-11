import pandas as pd
import joblib
import os
from sklearn.model_selection import train_test_split
from google.cloud import storage
from sklearn.linear_model import LogisticRegression
from datetime import datetime
from sklearn.metrics import precision_recall_fscore_support, accuracy_score


def load_processed_data(
        project_id: str,
        bucket_name: str,
        processed_data_file_path: str,
    ) -> pd.DataFrame:
    """Function to load data from GCS bucket."""
    try:
    
        if not all([project_id, bucket_name, processed_data_file_path]):
            print("Error: Missing one or more required environment variables.")
            return pd.DataFrame()

        print("--- Configuration ---")
        print(f"Project ID: {project_id}")
        print(f"Bucket Name: {bucket_name}")
        print(f"Processed Data File Path: {processed_data_file_path}")
        print("---------------------")

        storage_client = storage.Client(project=project_id)
        bucket = storage_client.bucket(bucket_name)
        df = pd.read_csv(processed_data_file_path)
        print(f"Loaded {len(df)} records from {processed_data_file_path}.")

        return True, "Data loaded successfully.", df
    except Exception as e:
        return False, f"ERROR: Failed to load data from {processed_data_file_path}. Details: {e}", pd.DataFrame()


def train_model(
    df: pd.DataFrame,
    algorithm: str = "logistic_regression" 
):
    """Function to train model."""

    try:

        X = df.drop('Churn', axis=1)
        y = df['Churn']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=7)
        model = get_model(algorithm)
        model.fit(X_train, y_train)

        return True, "Model training completed successfully.", model, X_test, y_test
    except Exception as e:
        return False, f"ERROR: Failed to train model. Details: {e}"


def get_model(algorithm: str):
    """Function to get model."""
    if algorithm == "logistic_regression":
        return LogisticRegression(random_state=7)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    

def export_model(
        project_id: str,
        bucket_name: str,
        stage_model_folder_path: str,
        algorithm: str,
        timestamp: str,
        model):
    """Function to export model to GCS."""
    try:

        print("--- Configuration ---")
        print(f"Project ID: {project_id}")
        print(f"Bucket Name: {bucket_name}")
        print(f"Stage Model Folder Path: {stage_model_folder_path}")
        model_file_name = f"model_{algorithm}_{timestamp}.joblib"
        model_path = f"gs://{bucket_name}/{stage_model_folder_path}{model_file_name}"
        print(f"Model will be saved to: {model_path}")

        # Save model locally first
        joblib.dump(model, model_file_name)
        print(f"Model saved locally to: {model_file_name}")

        # Upload to GCS
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(f"{stage_model_folder_path}{model_file_name}")
        blob.upload_from_filename(model_file_name)
        print(f"Model uploaded to GCS at: {model_path}")

        # Clean up local file
        os.remove(model_file_name)
        print(f"Local file {model_file_name} deleted.")

        return True, f"Model exported to {model_path}"
    except Exception as e:
        return False, f"ERROR: Failed to export model to {model_path}. Details: {e}"
    


def export_model_perormance(
        project_id: str,
        bucket_name: str,
        stage_model_folder_path: str,
        algorithm: str,
        timestamp: str,
        model,
        X_test,
        y_test):
    """Function to export model to GCS."""

    model_evaluation_file_name = f"model_evaluation_{algorithm}_{timestamp}.csv"
    model_evaluation_file_path = f"gs://{bucket_name}/{stage_model_folder_path}{model_evaluation_file_name}"
    
    try:

        print("--- Configuration ---")
        print(f"Project ID: {project_id}")
        print(f"Bucket Name: {bucket_name}")
        print(f"Stage Model Folder Path: {stage_model_folder_path}")
        print(f"Model evaluation will be saved to: {model_evaluation_file_path}")

        y_pred = model.predict(X_test)
        labels=[0, 1]
        
        precision, recall, f1_score, support = precision_recall_fscore_support(
        y_test, y_pred, labels=labels)

        overall_accuracy = accuracy_score(y_test, y_pred)

        evaluation_df = pd.DataFrame({
        'Class': labels,
        'Precision': precision,
        'Recall': recall,
        'F1-Score': f1_score,
        'Support': support,
        'Accuracy': [overall_accuracy] * len(labels),
        "algorithm": algorithm,
        "timestamp": timestamp
        })
        
        print(f"Metrics DataFrame:\n{evaluation_df}")

        # Upload to GCS
        evaluation_df.to_csv(model_evaluation_file_path, index=False)
        print(f"Model evaluation uploaded to GCS at: {model_evaluation_file_path}")
        return True, f"Model evaluation exported to {model_evaluation_file_path}"
    except Exception as e:
        return False, f"ERROR: Failed to export model evaluation to {model_evaluation_file_path}. Details: {e}"