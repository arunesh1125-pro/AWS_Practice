import json
import boto3
from boto3.dynamodb.types import TypeDeserializer


def lambda_handler(event, context):
    deserializer = TypeDeserializer()

    # Process all incoming stream rows
    for record in event.get("Records", []):
        event_name = record["eventName"]  # INSERT, MODIFY, REMOVE
        ddb_data = record.get("dynamodb", {})

        new_image = ddb_data.get("NewImage", {})
        old_image = ddb_data.get("OldImage", {})

        # Clear out DynamoDB type descriptors
        new_item = (
            {k: deserializer.deserialize(v) for k, v in new_image.items()}
            if new_image
            else {}
        )
        old_item = (
            {k: deserializer.deserialize(v) for k, v in old_image.items()}
            if old_image
            else {}
        )

        if event_name == "INSERT":
            print(f"[INSERT] Stream found new item: {new_item}")
            handle_new_reading(new_item)
        elif event_name == "MODIFY":
            print(f"[MODIFY] Entry updated from {old_item} to {new_item}")
        elif event_name == "REMOVE":
            print(f"[REMOVE] Deleted data row: {old_item}")


def handle_new_reading(item):
    # Checking for String 'TRUE' or 'true' to match the database index constraint
    alert_status = str(item.get("drowsyAlert", "")).upper()
    if alert_status == "TRUE":
        print(f"⚠️ ALERT: Device {item['deviceId']} is drowsy!")
