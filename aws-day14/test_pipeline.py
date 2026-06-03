from decimal import Decimal
import boto3

# Initialize the DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('SensorReadings')

print("Sending live mock event to DynamoDB...")

# This write event will travel through your Stream directly into Lambda
table.put_item(
    Item={
        'deviceId': 'device_stream_live_999',
        'drowsyAlert': 'TRUE',
        'earpValue': Decimal('0.14'),
        'timestamp': '2026-06-04T01:00:00Z'
    }
)

print("Item written successfully! The streaming pipeline is processing it.")
