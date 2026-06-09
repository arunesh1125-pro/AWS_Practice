import boto3
import json
import time

sf_client = boto3.client('stepfunctions', region_name='ap-south-1')
ACCOUNT_ID = "859977947607" # 👈 Replace with your real Account ID

def launch_training_job():
    sm_arn = f"arn:aws:states:ap-south-1:{ACCOUNT_ID}:stateMachine:ml-training-pipeline"
    
    # Generate unique execution trace name using a timestamp
    execution_name = f"training-run-{int(time.time())}"
    
    input_payload = {
        'datasetKey': 'datasets/june-2026/train.csv',
        'modelType':  'xgboost',
        'hyperparams': {'n_estimators': 100, 'max_depth': 6}
    }
    
    response = sf_client.start_execution(
        stateMachineArn=sm_arn,
        name=execution_name,
        input=json.dumps(input_payload)
    )
    
    print(f"🚀 Execution launched successfully!")
    print(f"Trace Name: {execution_name}")
    print(f"Execution ARN: {response['executionArn']}")

if __name__ == "__main__":
    launch_training_job()
