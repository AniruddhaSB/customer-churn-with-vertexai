import glob
import os
import pandas as pd
from flask import Flask, request
from datetime import datetime
from dotenv import load_dotenv

from load_data import load_data



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
        raw_data_folder_path=os.getenv("RAW_DATA_FOLDER_PATH", "gs://customer-churn-demo/data/raw/")
    )
    if raw_data.empty is True:
        return "No data loaded."
    else:
        return f"Loaded {len(raw_data)} records."
    
    
# This block must be at the same level of indentation as the import statement and app = Flask(__name__)
if __name__ == '__main__':
    # Get the port from the environment variable, defaulting to 8080 if not found
    port = int(os.environ.get('PORT', 8080))
    load_dotenv()
    app.run(host='0.0.0.0', port=port, debug=True)