import boto3
import os

s3_client = boto3.client('s3')
filepath = 'aws-day2\model\iris_model.joblib'
bucket = 'arunesh-ml-bucket1-2026'
keys = 'datasets/sample_data.csv'

s3_client.upload_file(
    filepath,
    bucket,
    keys,
    Config=boto3.transfer.TransferConfig(
        multipart_threshold = 100 * 1024 * 1024,   # 100 MB threshold
        max_concurrency = 10,               # 10 parallel uploads
        multipart_chunksize = 50 * 1024 * 1024   # 50 MB per part
    )
)