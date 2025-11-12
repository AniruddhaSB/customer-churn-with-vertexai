# Functionalities:

## Load Data:

1. This operation is to load data from GCS bucket.
2. All the CSV files in the said bucket will be loaded in a single data frame.
3. Asssumption: All CSVs match same schema / columns etc.
4. Finally a Pandas dataframe is returned as output.
5. Endpoint - 
```code
HTTP GET
NO Query String Parameters

/load_data
```

## Data Preprocessing:

1. Logical extension of load data operation.
2. Loads the data and then process the data.
3. Performs all preprocessing tasks - 
    - Drop rows with missing values
    - Drop duplicate rows
    - Feature engineer: Add new columns "RecentlyActive" (binary value), 
    ```code
    if "Last Interaction" < 5 then 1 else 0
    ```
    - Feature engineer: Add new columns "HighSupportUser" (binary value), 
    ```code
    if "Support Calls" > 5 then 1 else 0
4. Apply StandardScalar to all numerical columns except Churn (output column) and newly added binary feature columns namely "RecentlyActive" and "HighSupportUser".
5. Apply LabelEncoder to all the categorical columns.
6. Finally the preprocessed data along with the scalar and encoder ill be exported for further processing.
7. Endpoint -
```code
HTTP GET
NO Query String Parameters

/lnp_data
```

## Model Training:
1. Read in the processed data.
2. Split data and train logistic_regression model.
3. Finally export the model, scalar and encoder to GCS.
4. It also evaluates the model performance matrix for binary classification and export it to GCS. For e.g. see - 
5. Endpoint -
```code
HTTP GET
NO Query String Parameters

/train
```

## Publish Model
1. Read in the current production model performance (if present).
2. Read in the latest model evaluation from staging.
3. Compare model performance (for positive class) across multiple measures (e.g. - F1-Score, Accuracy)
4. If all measures are improved/better then model will be promoted from stage to prod.
5. If any of the measure is degraded, model will not be promoted to production.
6. Along with model, evaluation will be promoted to production are in GCS too.
7. Stage model and evaluations will be kept as is for backup/ fallbacks.
8. Endpoint -
```code
HTTP GET
NO Query String Parameters

/publish
```

## Model Serving:
1. API is created to expose the model for real time consumption / use ./ inferencing.
2. We load query string parameters into a dataframe - as user input record.
3. We load pretrained model from model/prod and use it to predict the output for new record.
4. We load pretrained scalar() pkl/pickle file and use the same scalar to transform the new input values as part of preprocessing.
5. We load pretrained encoder() pkl/pickle file and use the smae encoder to transform the new input values as part of preprocessing.
6. We pass this user input (dataframe with single record) as is from the preprocessing step. This will help do same transformations and feature engineering.
7. Processed data is then used for prediction using the pretrained model. 
8. Endpoint -
```code
HTTP Get
Query String Parameters (all are required, no default / error handling is done)

/predict

Churn = 1 example - 
?CustomerID=1&Age=39&Gender=Male&Tenure=12&Usage%20Frequency=4&Support%20Calls=3&Payment%20Delay=12&Subscription%20Type=Basic&Contract%20Length=Monthly&Total%20Spend=357&Last%20Interaction=15&Churn=1

Churn = 0 example - 
?CustomerID=1&Age=39&Gender=Male&Tenure=12&Usage%20Frequency=4&Support%20Calls=3&Payment%20Delay=12&Subscription%20Type=Basic&Contract%20Length=Monthly&Total%20Spend=357&Last%20Interaction=15&Churn=1

Note: CustomerID and Churn are useless inputs, will be dropped while preprocessing, so it can be any value.

```
# Other Important Points:

## Application Default Credentials:
1. Refer [Set up Application Default Credentials](https://docs.cloud.google.com/docs/authentication/provide-credentials-adc#how-to) for actual details.
2. Use existing / create new service account. Here I created a new service account.
3. Provide access to this service account to work with expected cloud resource (GCS bucket in this case).
4. Create JSON Key for the service account. This key will be used by code as a ADC to access cloud resources.
5. Configure cloud run to use this service account to run the container.
6. Refer [this image](DocumentationImages\ServiceAccountSetupForCloudRunToAccessGCS.bmp) for details regarding this setup.

## Docker image:
1. Build docker image refering to environment variables from .env file - 
```code
docker build -t customer-churn-prediction .
```
2. To run container image use below docker command. 
```code
docker run -p 8080:8080 --env-file .env customer-churn-prediction
```


## References:
1. Original dataset and project info can be found [here](https://www.kaggle.com/datasets/muhammadshahidazeem/customer-churn-dataset) 
2. Data downloaded has 2 files. One for training data and another one for testing data.
3. We use only training data for iniital trining. 
4. Using online tool - mightymerge.io, split the input file into multiple onces.
5. I have made each file having 50k records. So using downloaded file customer_churn_dataset-training-master.csv. I was able to create 9 files.
6. Preprocessing code is inspired from - https://www.kaggle.com/code/youssefmoustafa21/customer-churn-prediction-99-accuracy

