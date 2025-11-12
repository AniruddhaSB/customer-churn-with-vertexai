import pandas as pd
from google.cloud import storage

def get_model_evaluation_metrics(
        project_id: str,
        bucket_name: str,
        model_folder_path: str,
    ):

    """Function to load model evaluation data from GCS bucket."""
    if not all([project_id, bucket_name, model_folder_path]):
        print("Error: Missing one or more required environment variables.")
        return pd.DataFrame()

    print("--- Configuration ---")
    print(f"Project ID: {project_id}")
    print(f"Bucket Name: {bucket_name}")
    print(f"Model Evaluation Folder Path: {model_folder_path}")
    print("---------------------")

    try:
        #1. Read most recent evaluation CSV files from the specified GCS folder
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=model_folder_path)
        
        latest_blob = None
        latest_creation_time = None
        for blob in blobs:
            if blob.name.endswith(".csv"):
                if latest_blob is None or blob.time_created > latest_creation_time:
                    latest_blob = blob
                    latest_creation_time = blob.time_created

        if latest_blob is None:
            print(f"No model evaluation CSV files found in GCS folder: {model_folder_path}")
            return True, pd.DataFrame(), None
        
        df = pd.read_csv(f"gs://{bucket_name}/{latest_blob.name}")
        print(f"Loaded model evaluation data from {latest_blob.name}.")
        print(f"Loaded Model Evaluation Data:\n{df}")
        return True, df, latest_blob
    except Exception as e:
        print(f"ERROR: Failed to load model evaluation data from {model_folder_path}. Details: {e}")
        return False, pd.DataFrame(), None

    
def move_model_from_stage_to_prod(
        project_id: str,
        bucket_name: str,
        stage_model_folder_path: str,
        stage_eval_blob: any,
        prod_model_folder_path: str,
    ):

    """Function to load model evaluation data from GCS bucket."""
    if not all([project_id, bucket_name, stage_model_folder_path, prod_model_folder_path, stage_eval_blob]):
        print("Error: Missing one or more required environment variables.")
        return pd.DataFrame()
    
    print("--- Configuration ---")
    print(f"Project ID: {project_id}")
    print(f"Bucket Name: {bucket_name}")
    print(f"Stage Model Folder Path: {stage_model_folder_path}")
    print(f"Stage Evaluation Blob: {stage_eval_blob}")
    print(f"Prod Model Folder Path: {prod_model_folder_path}")
    print("---------------------")

    try:
        stage_eval_blob_name = stage_eval_blob.name
        print(f"Stage Evaluation Blob Name: {stage_eval_blob_name}")

        # Get Model Name From Eval Path
        stage_model_blob_name = stage_eval_blob_name.replace("_evaluation_", "_").replace(".csv", ".joblib")
        print(f"Stage Model Path: {stage_model_blob_name}")
        
        #Destination Blob names
        prod_eval_blob_name = stage_eval_blob_name.replace("stage", "prod")
        prod_model_blob_name = stage_model_blob_name.replace("stage", "prod")
        print(f"Prod Eval Blob Name: {prod_eval_blob_name}")
        print(f"Prod Model Blob Name: {prod_model_blob_name}")

        storage_client = storage.Client(project=project_id)
        bucket = storage_client.bucket(bucket_name)
        stage_model_blob = bucket.blob(stage_model_blob_name)

        bucket.copy_blob(stage_model_blob, bucket, prod_model_blob_name)
        print(f"Moved model file from {stage_model_blob_name} to {prod_model_blob_name}")
        
        bucket.copy_blob(stage_eval_blob, bucket, prod_eval_blob_name)
        print(f"Moved evaluation file from {stage_eval_blob.name} to {prod_eval_blob_name}")

        # Donot deleet, keep it for backup.

        return True, "Model and evaluation files moved successfully.", prod_model_blob_name
    except Exception as e:
        print(f"ERROR: Failed to move model and evaluation file from {stage_eval_blob.name} Details: {e}")
        return False, f"ERROR: Failed to move model and evaluation file from {stage_eval_blob.name} Details: {e}", stage_model_blob_name


def compare_model_performances(
        prod_model_evaluation_df: pd.DataFrame,
        stage_model_evaluation_df: pd.DataFrame,
        comparison_metric: str = ["Accuracy", "F1-Score"]
    ):
    """Function to compare model performances."""
    try:
        # Compare for class 1 (positive class)
        prod_model_evaluation_df = prod_model_evaluation_df[prod_model_evaluation_df["Class"] == 1]
        stage_model_evaluation_df = stage_model_evaluation_df[stage_model_evaluation_df["Class"] == 1]

        df_result = pd.DataFrame()
        for metric in comparison_metric:
            df_result[f"Change_in_{metric}"] = prod_model_evaluation_df[metric] - stage_model_evaluation_df[metric]
        
            if(df_result[df_result[f"Change_in_{metric}"] > 0].empty is False):
                print(f"for measure {metric}, Production model is better than satge model.")
            else:
                print(f"for measure {metric}, Production model is NOT better than satge model. Not promoting the model.")
                return False, f"for measure {metric}, Production model is NOT better than satge model. Not promoting the model."
        
        print(f"Model Performance Comparison:\n{df_result}")
        return True, "Production model performance is better than stage model performance."

    except Exception as e:
        print(f"ERROR: Failed to compare model performances. Details: {e}")
        return False, f"ERROR: Failed to compare model performances. Details: {e}", pd.DataFrame() 

