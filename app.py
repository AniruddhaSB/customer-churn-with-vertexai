import glob
import os
from flask import Flask, request
from datetime import datetime

import pandas as pd

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

# This block must be at the same level of indentation as the import statement and app = Flask(__name__)
if __name__ == '__main__':
    # Get the port from the environment variable, defaulting to 5000 if not found
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)