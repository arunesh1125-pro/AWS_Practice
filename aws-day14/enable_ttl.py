import boto3
from botocore.exceptions import ClientError

dynamodb_client = boto3.client("dynamodb", region_name="ap-south-1")
table_name = "UserSessions"

try:
    print(f"Enabling TTL tracking on attribute 'expiresAt'...")
    dynamodb_client.update_time_to_live(
        TableName=table_name,
        TimeToLiveSpecification={"Enabled": True, "AttributeName": "expiresAt"},
    )
    print("TTL configuration request submitted successfully.")
except ClientError as e:
    print(f"Status: {e.response['Error']['Message']}")
