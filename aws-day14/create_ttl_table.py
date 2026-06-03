import boto3
from botocore.exceptions import ClientError

region = "ap-south-1"
dynamodb = boto3.client("dynamodb", region_name=region)
table_name = "UserSessions"

try:
    print(f"Creating table '{table_name}'...")
    dynamodb.create_table(
        TableName=table_name,
        KeySchema=[{"AttributeName": "sessionId", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "sessionId", "AttributeType": "S"},
            {"AttributeName": "userId", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "UserIndex",
                "KeySchema": [{"AttributeName": "userId", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    print("Waiting for table to become ACTIVE...")
    dynamodb.get_waiter("table_exists").wait(TableName=table_name)
    print("Table successfully created with GSI!")
except ClientError as e:
    print(f"Error: {e.response['Error']['Message']}")
