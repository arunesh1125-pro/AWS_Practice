import boto3

dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
table = dynamodb.Table("SensorReadings")

print("Pushing a drowsy driver record to trigger the live stream...")
table.put_item(
    Item={
        "deviceId": "device_stream_abc",
        "drowsyAlert": True,
        "earpValue": 0.15,
        "timestamp": "2026-06-02T02:00:00Z",
    }
)
print("Item safely saved! The DynamoDB Stream has caught this event.")
import boto3

dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
table = dynamodb.Table("SensorReadings")

print("Pushing a drowsy driver record to trigger the live stream...")
table.put_item(
    Item={
        "deviceId": "device_stream_abc",
        "drowsyAlert": True,
        "earpValue": 0.15,
        "timestamp": "2026-06-02T02:00:00Z",
    }
)
print("Item safely saved! The DynamoDB Stream has caught this event.")
