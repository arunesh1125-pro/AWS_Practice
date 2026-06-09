import boto3
import json

def setup_eventbridge_infrastructure():
    # Initialize the EventBridge client
    events_client = boto3.client('events', region_name='ap-south-1')
    
    print("--- Starting EventBridge Infrastructure Provisioning ---")

    # 1. Create the Custom Event Bus
    bus_response = events_client.create_event_bus(
        Name='ml-platform-bus',
        Description='Event bus for all ML pipeline events'
    )
    print(f"✅ Custom Bus Active: {bus_response['EventBusArn']}")

    # 2. Configure Rule 1: High Accuracy Deployment
    events_client.put_rule(
        Name='deploy-high-accuracy-models',
        EventBusName='ml-platform-bus',
        EventPattern=json.dumps({
            'source':      ['com.mycompany.mlplatform'],
            'detail-type': ['ModelTrained'],
            'detail': {
                'accuracy': [{'numeric': ['>=', 0.90]}]
            }
        }),
        State='ENABLED',
        Description='Trigger deployment for models with accuracy >= 90%'
    )
    
    events_client.put_targets(
        Rule='deploy-high-accuracy-models',
        EventBusName='ml-platform-bus',
        Targets=[{
            'Id':  'deploy-lambda',
            'Arn': 'arn:aws:lambda:ap-south-1:859977947607:function:deploy-model'  # 👈 Replace with actual Lambda ARN
        }]
    )
    print("✅ Rule 1 (High Accuracy) and Target linked successfully.")

    # 3. Configure Rule 2: Model Failure Alerts
    events_client.put_rule(
        Name='alert-on-model-failure',
        EventBusName='ml-platform-bus',
        EventPattern=json.dumps({
            'source':      ['com.mycompany.mlplatform'],
            'detail-type': ['ModelFailed']
        }),
        State='ENABLED'
    )
    
    events_client.put_targets(
        Rule='alert-on-model-failure',
        EventBusName='ml-platform-bus',
        Targets=[{
            'Id':  'sns-alert',
            'Arn': 'arn:aws:sns:ap-south-1:859977947607:ml-ops-alerts'  # 👈 Replace with actual SNS Topic ARN
        }]
    )
    print("✅ Rule 2 (Failure Alerts) and Target linked successfully.")

    # 4. Configure Rule 3: Scheduled Retraining (Runs on default bus)
    events_client.put_rule(
        Name='weekly-model-retraining',
        EventBusName='default',
        ScheduleExpression='cron(0 0 ? * SUN *)',
        State='ENABLED'
    )
    
    events_client.put_targets(
        Rule='weekly-model-retraining',
        EventBusName='default',
        Targets=[{
            'Id':  'retrain-lambda',
            'Arn': 'arn:aws:lambda:ap-south-1:859977947607:function:trigger-retraining',  # 👈 Replace with actual Retain Lambda ARN
            'Input': json.dumps({'scheduled': True, 'trigger': 'weekly-cron'})
        }]
    )
    print("✅ Rule 3 (Scheduled Rule) and Target linked on default bus.")
    print("--- Infrastructure Provisioning Complete ---")

if __name__ == "__main__":
    setup_eventbridge_infrastructure()
