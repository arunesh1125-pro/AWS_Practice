import boto3
from botocore.exceptions import ClientError

region = "ap-south-1"
sqs = boto3.client("sqs", region_name=region)
dynamodb = boto3.client("dynamodb", region_name=region)
sts = boto3.client("sts")

# Fetch your real AWS Account ID dynamically
account_id = sts.get_caller_identity()["Account"]

# 1. Create DynamoDB Table for Idempotent Checks
try:
    print("Creating DynamoDB tracking table 'ProcessedReadings'...")
    dynamodb.create_table(
        TableName="ProcessedReadings",
        KeySchema=[{"AttributeName": "readingId", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "readingId", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST"
    )
    dynamodb.get_waiter("table_exists").wait(TableName="ProcessedReadings")
    print("DynamoDB tracking table is ACTIVE.")
except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceInUseException":
        print("DynamoDB table already exists.")

# 2. Create Standard SQS Queue
print("Creating Standard SQS Queue...")
std_queue = sqs.create_queue(QueueName="SensorReadingsQueue")
print(f"Standard Queue URL: {std_queue['QueueUrl']}")

# 3. Create FIFO SQS Queue (Must enable Content-Based Deduplication or provide DeduplicationId)
print("Creating FIFO SQS Queue...")
fifo_queue = sqs.create_queue(
    QueueName="OrdersQueue.fifo",
    Attributes={
        "FifoQueue": "true",
        "ContentBasedDeduplication": "false"  # Explicitly using your custom tracking ID formula
    }
)
print(f"FIFO Queue URL: {fifo_queue['QueueUrl']}")
print("\nInfrastructure Setup Complete!")
