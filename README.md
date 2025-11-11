# Functionalities:

## Load Data:

1. This operation is to load data from GCS bucket.
2. All the CSV files in the said bucket will be loaded in a single data frame.
3. Asssumption: All CSVs match same schema / columns etc.
4. Finally a Pandas dataframe is returned as output.

## Next Functionality:

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
3. We use only training data for iniital trining (we split it into 2 train and test sets ourselves)

