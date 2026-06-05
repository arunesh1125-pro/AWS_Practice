import json
import time
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr

region = "ap-south-1"
sqs = boto3.client("sqs", region_name=region)
dynamodb = boto3.resource("dynamodb", region_name=region)
table = dynamodb.Table("ProcessedReadings")

# Get standard queue URL dynamically
queue_url = sqs.get_queue_url(QueueName='SensorReadingsQueue')['QueueUrl']

def process_sensor_reading(message_body):
    reading = json.loads(message_body)
    reading_id = reading["readingId"]

    try:
        # Idempotency safety guard logic check
        table.put_item(
            Item={
                "readingId": reading_id,
                "deviceId": reading["deviceId"],
                "processed": True,
                "processedAt": datetime.now(timezone.utc).isoformat() + "Z"
            },
            ConditionExpression=Attr("readingId").not_exists()
        )
        print(f"✅ Success: Processed new reading: {reading_id}")

    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            print(f"⚠️ Duplicate detected: Reading {reading_id} has already been processed.")
        else:
            print(f"Error processing reading {reading_id}: {e.response['Error']['Message']}")

# --- Simulation Execution Workflow ---
mock_payload = {"readingId": "read-999-xyz", "deviceId": "sensor-01"}

print("Sending sensor reading payload to Standard Queue...")
sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(mock_payload))

print("\nProcessing message for the first time...")
process_sensor_reading(json.dumps(mock_payload))

print("\nSimulating network duplicate retry event delivery...")
process_sensor_reading(json.dumps(mock_payload))