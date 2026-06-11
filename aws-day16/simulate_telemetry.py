import boto3
import json
from datetime import datetime
import time

kinesis = boto3.client('kinesis', region_name='ap-south-1')
STREAM_NAME = 'vehicle-telemetry'

def send_telemetry_batch():
    print("--- 🚗 Starting Telemetry Production Broadcast ---")
    
    # Bundle data profiles mimicking 3 unique vehicles on the road
    telemetry_batch = [
        {
            'deviceId': 'VEHICLE-01',
            'earpValue': 0.35, # Fully awake driver
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        },
        {
            'deviceId': 'VEHICLE-02', 
            'earpValue': 0.12, # 🚨 Drowsy driver profile (Should trigger alert!)
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        },
        {
            'deviceId': 'VEHICLE-03',
            'earpValue': 0.42, # Fully awake driver
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    ]
    
    records = []
    for reading in telemetry_batch:
        records.append({
            'Data': json.dumps(reading).encode('utf-8'),
            'PartitionKey': reading['deviceId'] # Same vehicle ID locks into identical shard for ordering
        })
        
    response = kinesis.put_records(
        StreamName=STREAM_NAME,
        Records=records
    )
    
    print(f"🚀 Sent batch of {len(records)} vehicle data streams into Kinesis cluster.")
    print(f"Failed count response record: {response.get('FailedRecordCount', 0)}")

if __name__ == "__main__":
    send_telemetry_batch()
