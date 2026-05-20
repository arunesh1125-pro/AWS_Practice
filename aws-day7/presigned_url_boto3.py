import boto3
from datetime import datetime

s3_client = boto3.client('s3', region_name = 'ap-south-1')

# generate a presigned url for downloading (Get)
download_url = s3_client.generate_presigned_url(
    ClientMethod = 'get_object',
    Params = {
        'Bucket': 'arunesh-private-bucket',
        'Key': 'reports/q1-finacial-report.pdf'
    },
    ExpiresIn = 3600 # 1 hour in seconds
)

print(download_url)

# Generate a presigned URL for uploading (PUT)
upload_url = s3_client.generate_presigned_url(
    ClientMethod='put_object',
    Params={
        'Bucket': 'arunesh-private-bucket',
        'Key': 'uploads/user-123-profile-photo.jpg',
        'ContentType': 'image/jpeg'
    },
    ExpiresIn=300  # 5 minutes to complete the upload
)

# Send this URL to the user's browser
# They PUT their file directly to S3 — never goes through your server