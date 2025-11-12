from google.cloud import aiplatform

def register_model(
        project_id: str,
        bucket_name: str,
        prod_model_folder_path: str,
        model_display_name: str,
):
    """Function to register model."""
    try:

        aiplatform.init(project=project_id, location="us-central1")

        model = aiplatform.Model.upload(
            display_name=model_display_name,
            artifact_uri=f"gs://{bucket_name}/{prod_model_folder_path}",
            serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.0-24:latest",
            sync=True
        )

        print(f"Model registered successfully with name: {model.display_name} and ID: {model.resource_name}")
        return True, f"Model registered successfully with name: {model.display_name} and ID: {model.resource_name}"
    except Exception as e:
        print(f"ERROR: Failed to register model. Details: {e}")
        return False, f"ERROR: Failed to register model. Details: {e}",