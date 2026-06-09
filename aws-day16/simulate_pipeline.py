import boto3
import json

events_client = boto3.client('events', region_name='ap-south-1')

def publish_model_event(model_id, event_type, accuracy, metadata=None):
    """Broadcasts ML Pipeline lifecycle data over EventBridge."""
    payload = {
        'modelId':   model_id,
        'accuracy':  accuracy,
        'version':   'v5',
        'metadata':  metadata or {}
    }
    
    response = events_client.put_events(
        Entries=[{
            'EventBusName': 'ml-platform-bus',
            'Source':       'com.mycompany.mlplatform',
            'DetailType':   event_type,
            'Detail':       json.dumps(payload),
            'Resources': [
                f'arn:aws:s3:::ml-models/{model_id}'
            ]
        }]
    )
    
    failed_count = response.get('FailedEntryCount', 0)
    if failed_count > 0:
        print(f"❌ Failed to publish event for {model_id}: {response['Entries']}")
    else:
        event_id = response['Entries'][0]['EventId']
        print(f"🚀 Sent [{event_type}] for {model_id}. Event ID: {event_id}")

if __name__ == "__main__":
    print("--- Simulating Live ML Pipeline Runs ---")
    
    # Run 1: High Accuracy Production Event (Should trigger deployment)
    publish_model_event('xgboost-v5', 'ModelTrained', accuracy=0.94)
    
    # Run 2: Low Accuracy Filter Event (Should be dropped silently)
    publish_model_event('lstm-v2', 'ModelTrained', accuracy=0.76)
    
    # Run 3: Failure Alert Event (Should trigger downstream SNS alert)
    publish_model_event('xgboost-v4', 'ModelFailed', accuracy=0.0)
    
    print("--- Pipeline Simulation Completed ---")
