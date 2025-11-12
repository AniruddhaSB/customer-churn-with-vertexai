import glob
import os
import json
import pandas as pd
from flask import Flask, request
from datetime import datetime
from dotenv import load_dotenv

from load_data import load_data
from preprocess_data import preprocess_data, save_processed_data, save_scalar, save_encoder
from train_model import load_processed_data, train_model, export_model, export_model_perormance
from host_model import get_model_evaluation_metrics, move_model_from_stage_to_prod, compare_model_performances

app = Flask(__name__)

@app.route('/')
def hello_world():
    # Get the current date and time
    current_time = datetime.now()

    # Format the date and time as a string
    # %Y = Year, %m = Month, %d = Day, %H = Hour, %M = Minute, %S = Second
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

    # Create the final response string
    response = f'Namaste. Current date and time is: {formatted_time}'

    return response

@app.route('/load_data', methods=['GET'])
def load_data_api():


    raw_data = load_data(
        project_id=os.getenv("PROJECT_ID", "nimble-octagon-253816"),
        bucket_name=os.getenv("BUCKET_NAME", "customer-churn-demo"),
        raw_data_folder_path=os.getenv("RAW_DATA_FOLDER_PATH", "data/raw/")
    )
    if raw_data.empty is True:
        return "No data loaded."
    else:
        return f"Loaded {len(raw_data)} records."

@app.route('/lnp_data', methods=['GET'])
def preprocess_data_api():

    messages = ["Load and Process Data"]
    raw_data = load_data(
        project_id=os.getenv("PROJECT_ID", "nimble-octagon-253816"),
        bucket_name=os.getenv("BUCKET_NAME", "customer-churn-demo"),
        raw_data_folder_path=os.getenv("RAW_DATA_FOLDER_PATH", "data/raw/")
    )

    if raw_data.empty is True:
        messages.append("No data loaded.")
        return "\n".join(messages)
    messages.append(f"Loaded {len(raw_data)} records.")

    processed_data, scaler, le = preprocess_data(
        df=raw_data
    )

    if processed_data.empty is True:
        messages.append("No data after preprocessing.")
        return "\n".join(messages)
    messages.append(f"Loaded {len(raw_data)} records. After preprocessing data has {len(processed_data)} records.")

    outcome, msg = save_processed_data(
        project_id=os.getenv("PROJECT_ID", "nimble-octagon-253816"),
        bucket_name=os.getenv("BUCKET_NAME", "customer-churn-demo"),
        processed_data_folder_path=os.getenv("PROCESSED_DATA_FOLDER_PATH", "data/processed/"),
        df=processed_data
    )
    if outcome:
        messages.append("Processed data saved successfully.")
    else:
        messages.append(msg)
        return "\n".join(messages)
    
    save_scalar_outcome, save_scalar_message = save_scalar(
        project_id=os.getenv("PROJECT_ID", "nimble-octagon-253816"),
        bucket_name=os.getenv("BUCKET_NAME", "customer-churn-demo"),
        processed_data_folder_path=os.getenv("PROCESSED_DATA_FOLDER_PATH", "data/processed/"),
        scaler=scaler
    )
    if save_scalar_outcome:
        messages.append("Scalar saved successfully.")
    else:
        messages.append(save_scalar_message)
        return "\n".join(messages)
    
    save_encoder_outcome, save_encoder_message = save_encoder(
        project_id=os.getenv("PROJECT_ID", "nimble-octagon-253816"),
        bucket_name=os.getenv("BUCKET_NAME", "customer-churn-demo"),
        processed_data_folder_path=os.getenv("PROCESSED_DATA_FOLDER_PATH", "data/processed/"),
        encoder=le
    )
    if save_encoder_outcome:
        messages.append("Encoder saved successfully.")
    else:
        messages.append(save_encoder_message)
        return "\n".join(messages)

    json_object = {"messages": messages}
    return json.dumps(json_object)

@app.route('/train', methods=['GET'])
def train_model_api():

    messages = ["Train Model Started"]
    load_processed_data_outcome, load_msg, df = load_processed_data(
        project_id=os.getenv("PROJECT_ID", "nimble-octagon-253816"),
        bucket_name=os.getenv("BUCKET_NAME", "customer-churn-demo"),
        processed_data_file_path=os.getenv("PROCESSED_DATA_FILE_PATH", "gs://customer-churn-demo/data/processed/processed_data.csv")
    )
    if load_processed_data_outcome is False:
        return "No data loaded."
    messages.append(f"Processed data loaded successfully. Loaded {len(df)} records.")

    train_model_outcome, train_msg, model, X_test, y_test = train_model(
        df=df,
        algorithm="logistic_regression"
    )
    if train_model_outcome is False:
        messages.append(train_msg)
        return "\n".join(messages)
    messages.append(f"Model trained successfully.{train_msg}")

    timestamp = f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    export_model_outcome, export_model_msg = export_model(
        project_id=os.getenv("PROJECT_ID", "nimble-octagon-253816"),
        bucket_name=os.getenv("BUCKET_NAME", "customer-churn-demo"),
        stage_model_folder_path=os.getenv("STAGE_MODEL_FOLDER_PATH", "model/stage/"),
        algorithm="logistic_regression",
        timestamp=timestamp,
        model=model
    )
    if export_model_outcome is False:
        messages.append(export_model_msg)
        return "\n".join(messages)
    messages.append(f"Model exported successfully.{export_model_msg}")

    export_model_perormance_outcome, export_model_perormance_msg = export_model_perormance(
        project_id=os.getenv("PROJECT_ID", "nimble-octagon-253816"),
        bucket_name=os.getenv("BUCKET_NAME", "customer-churn-demo"),
        stage_model_folder_path=os.getenv("STAGE_MODEL_FOLDER_PATH", "model/stage/"),
        algorithm="logistic_regression",
        timestamp=timestamp,
        model=model,
        X_test=X_test,
        y_test=y_test
    )
    if export_model_perormance_outcome is False:
        messages.append(export_model_perormance_msg)
        return "\n".join(messages)
    messages.append(f"Model evaluation exported successfully.{export_model_perormance_msg}")


    json_object = {"messages": messages}
    return json.dumps(json_object)
    

@app.route('/publish', methods=['GET'])
def publish_model_api():

    messages = ["Publish Model Started"]
    prod_eval_load_outcome,prod_model_evaluation_df, prod_model_evaluation_blob = get_model_evaluation_metrics(
        project_id=os.getenv("PROJECT_ID", "nimble-octagon-253816"),
        bucket_name=os.getenv("BUCKET_NAME", "customer-churn-demo"),
        model_folder_path=os.getenv("PROD_MODEL_FOLDER_PATH", "model/prod/")
    )

    stage_eval_load_outcome, stage_model_evaluation_df, stage_model_evaluation_blob = get_model_evaluation_metrics(
        project_id=os.getenv("PROJECT_ID", "nimble-octagon-253816"),
        bucket_name=os.getenv("BUCKET_NAME", "customer-churn-demo"),
        model_folder_path=os.getenv("STAGE_MODEL_FOLDER_PATH", "model/stage/")
    )

    if prod_model_evaluation_df.empty is True:
        messages.append("No production model evaluation data found so publishing the latest stage model as is.")
        movement_outcome, movement_messgae, live_model = move_model_from_stage_to_prod(
            project_id=os.getenv("PROJECT_ID", "nimble-octagon-253816"),
            bucket_name=os.getenv("BUCKET_NAME", "customer-churn-demo"),
            stage_model_folder_path=os.getenv("STAGE_MODEL_FOLDER_PATH", "model/stage/"),
            stage_eval_blob=stage_model_evaluation_blob,
            prod_model_folder_path=os.getenv("PROD_MODEL_FOLDER_PATH", "model/prod/")
        )
        messages.append("Stage model promoted to production successfully.")
        messages.append(f"Current Model Served in Production:{live_model}")
    else:
        messages.append("Production model evaluation data found. Comparing stage and production model evaluations.")
        do_promote_new_model_to_prod, comparison_message = compare_model_performances(
            prod_model_evaluation_df=prod_model_evaluation_df,
            stage_model_evaluation_df=stage_model_evaluation_df,
            comparison_metric=["Accuracy", "F1-Score"]
        )
        messages.append(comparison_message)
        if do_promote_new_model_to_prod:
            messages.append("Promoting stage model to production.")
            movement_outcome, movement_messgae, live_model = move_model_from_stage_to_prod(
                project_id=os.getenv("PROJECT_ID", "nimble-octagon-253816"),
                bucket_name=os.getenv("BUCKET_NAME", "customer-churn-demo"),
                stage_model_folder_path=os.getenv("STAGE_MODEL_FOLDER_PATH", "model/stage/"),
                stage_eval_blob=stage_model_evaluation_blob,
                prod_model_folder_path=os.getenv("PROD_MODEL_FOLDER_PATH", "model/prod/")
            )
            messages.append("Stage model promoted to production successfully.")
            messages.append(f"Current Model Served in Production:{live_model}")
        else:
            messages.append("Stage model is not bettter, so NOT promoted to production.")
            messages.append(f"Current Model Served in Production:SAME AS BEFORE")

    json_object = {"messages": messages}
    return json.dumps(json_object)
    

# This block must be at the same level of indentation as the import statement and app = Flask(__name__)
if __name__ == '__main__':
    # Get the port from the environment variable, defaulting to 8080 if not found
    port = int(os.environ.get('PORT', 8080))
    load_dotenv()
    app.run(host='0.0.0.0', port=port, debug=True)