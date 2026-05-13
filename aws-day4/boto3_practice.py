import boto3
import pandas as pd
import io
import time

# Ex1: Read data from S3
def load_csv_from_s3(bucket_name, key):
    s3 = boto3.client('s3')

    # Get the object from S3
    response = s3.get_object(Bucket=bucket_name, Key=key)

    # Read the content of the object
    csv_content = response['Body'].read()

    # Convert bytes to a file-like object and read it into a DataFrame
    return pd.read_csv(io.BytesIO(csv_content))

# Ex2: Save model output to DynamoDB
def save_df_to_dynamodb(df, table_name, region='ap-south-1'):
    # Initialize DyamoDB resource
    dynamodb = boto3.resource('dynamodb', region_name=region)
    table = dynamodb.Table(table_name)

    # Get Current timestamp for real-time tracking
    current_timesstamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Iterate through rows and save to DynamodDB
    for index, row in df.iterrows():
        # Ensure native Python types (DynamoDB does not accept numpy float64/int64)
        user_id = f"user_{int(row['Unnamed: 0'])}"  # Converts index 0, 1, 2 into 'user_0', 'user_1'

        # extract model 
        prediction = str(int(row['label']))# Converts your label (0 or 1) to a string

        table.put_item(Item={
            'user_id': user_id,
            'prediction': prediction,
            'confidence': '1.0',  # Example confidence score, replace with actual if available
            'timestamp': current_timesstamp
        })
    print(f"Successfully uploaded {len(df)} predictions to {table_name} in DynamoDB.")

# Ex3: Using a named profile (for local dev)
session = boto3.Session(profile_name='client-dev')
s3 = session.client('s3')
response = s3.list_buckets()
for bucket in response['Buckets']:
    print(bucket['Name'])


# Usage
try:
    bucket_name = 'arunesh-ml-bucket1-2026'
    key= 'datasets/ml_data.csv'
    df = load_csv_from_s3(bucket_name, key)

    save_df_to_dynamodb(df, 'MLPredictions')

except Exception as e:
    print(f"An error occurred: {e}")