import boto3
import json

sf_client = boto3.client('stepfunctions', region_name='ap-south-1')

# Define your Account ID for easy string formatting
ACCOUNT_ID = "859977947607"  # 👈 Replace with your real AWS Account ID

state_machine_definition = {
    "Comment": "ML Model Training and Deployment Pipeline",
    "StartAt": "ValidateTrainingData",
    "States": {
        "ValidateTrainingData": {
            "Type": "Task",
            "Resource": f"arn:aws:lambda:ap-south-1:{ACCOUNT_ID}:function:validate-data",
            "Next": "TrainModel",
            "Retry": [{
                "ErrorEquals": ["Lambda.ServiceException", "Lambda.TooManyRequestsException"],
                "IntervalSeconds": 2,
                "MaxAttempts": 3,
                "BackoffRate": 2.0
            }],
            "Catch": [{
                "ErrorEquals": ["ValidationError"],
                "Next": "NotifyValidationFailure",
                "ResultPath": "$.error"
            }]
        },
        "TrainModel": {
            "Type": "Task",
            "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
            "Parameters": {
                "FunctionName": f"arn:aws:lambda:ap-south-1:{ACCOUNT_ID}:function:start-training",
                "Payload": {
                    "taskToken.$": "$$.Task.Token",
                    "input.$": "$"
                }
            },
            "HeartbeatSeconds": 3600,
            "TimeoutSeconds": 86400,
            "Next": "EvaluateModel"
        },
        "EvaluateModel": {
            "Type": "Task",
            "Resource": f"arn:aws:lambda:ap-south-1:{ACCOUNT_ID}:function:evaluate-model",
            "Next": "AccuracyCheck"
        },
        "AccuracyCheck": {
            "Type": "Choice",
            "Choices": [
                {
                    "Variable": "$.accuracy",
                    "NumericGreaterThanEquals": 0.90,
                    "Next": "DeployModel"
                },
                {
                    "Variable": "$.accuracy",
                    "NumericLessThan": 0.70,
                    "Next": "RejectModel"
                }
            ],
            "Default": "DeployModel" # Default fallback for this demo setup
        },
        "DeployModel": {
            "Type": "Task",
            "Resource": f"arn:aws:lambda:ap-south-1:{ACCOUNT_ID}:function:deploy-model",
            "End": True
        },
        "NotifyValidationFailure": {
            "Type": "Pass",
            "End": True
        },
        "RejectModel": {
            "Type": "Pass",
            "End": True
        }
    }
}

def deploy_pipeline():
    # 1. Create State Machine
    try:
        response = sf_client.create_state_machine(
            name='ml-training-pipeline',
            definition=json.dumps(state_machine_definition),
            roleArn=f'arn:aws:iam::{ACCOUNT_ID}:role/step-functions-execution-role', # 👈 Confirm exact role name
            type='STANDARD'
        )
        sm_arn = response['stateMachineArn']
        print(f"✅ State Machine Created Successfully!\nARN: {sm_arn}")
        return sm_arn
    except sf_client.exceptions.StateMachineAlreadyExists:
        sm_arn = f"arn:aws:states:ap-south-1:{ACCOUNT_ID}:stateMachine:ml-training-pipeline"
        print(f"ℹ️ State Machine already exists. Using: {sm_arn}")
        return sm_arn

if __name__ == "__main__":
    deploy_pipeline()
