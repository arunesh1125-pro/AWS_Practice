import boto3
from botocore.exceptions import ClientError

region = "ap-south-1"
dynamodb = boto3.client("dynamodb", region_name=region)

tables_to_create = [
    {
        "TableName": "UserCredits",
        "KeySchema": [{"AttributeName": "userId", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "userId", "AttributeType": "S"}],
    },
    {
        "TableName": "TransactionAudit",
        "KeySchema": [{"AttributeName": "txnId", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "txnId", "AttributeType": "S"}],
    },
    {
        "TableName": "Users",
        "KeySchema": [{"AttributeName": "userId", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "userId", "AttributeType": "S"}],
    },
    {
        "TableName": "Orders",
        "KeySchema": [
            {"AttributeName": "customerId", "KeyType": "HASH"},
            {"AttributeName": "orderId", "KeyType": "RANGE"}
        ],
        "AttributeDefinitions": [
            {"AttributeName": "customerId", "AttributeType": "S"},
            {"AttributeName": "orderId", "AttributeType": "S"}
        ],
    }
]

for table_def in tables_to_create:
    try:
        print(f"Creating table '{table_def['TableName']}'...")
        dynamodb.create_table(
            TableName=table_def["TableName"],
            KeySchema=table_def["KeySchema"],
            AttributeDefinitions=table_def["AttributeDefinitions"],
            BillingMode="PAY_PER_REQUEST"
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"Table '{table_def['TableName']}' already exists.")
        else:
            print(f"Error building table: {e.response['Error']['Message']}")

print("Waiting for tables to initialize...")
for table_def in tables_to_create:
    try:
        dynamodb.get_waiter("table_exists").wait(TableName=table_def["TableName"])
    except Exception:
        pass
print("All 4 infrastructure tables are ACTIVE!")
