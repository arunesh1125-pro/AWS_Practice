import boto3
import json
import time
import os

# Align workspace target file path strings
TEMPLATE_PATH = r'D:\AWS\aws-day19\ml-platform-template.yaml'
STACK_NAME = 'ml-platform-prod'
SET_NAME = 'add-sqs-queue-may-2026'

cf = boto3.client('cloudformation', region_name='ap-south-1')

def execute_pipeline():
    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(f"Missing required update template at: {TEMPLATE_PATH}")

    with open(TEMPLATE_PATH, 'r') as f:
        template_body = f.read()

    print("==================================================")
    print(" STEP 1: INITIALIZING CLOUDFORMATION CHANGE SET   ")
    print("==================================================")
    cf.create_change_set(
        StackName=STACK_NAME,
        TemplateBody=template_body,
        ChangeSetName=SET_NAME,
        Description='Adding SQS queue for async model inference',
        Parameters=[
            {'ParameterKey': 'Environment',      'ParameterValue': 'prod'},
            {'ParameterKey': 'LambdaMemorySize', 'ParameterValue': '1024'},
            {'ParameterKey': 'DBPassword',       'UsePreviousValue': True}
        ],
        Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM']
    )
    print(f"Change set register request sent: '{SET_NAME}'")

    print("\n==================================================")
    print(" STEP 2: WAITING FOR DELTA COMPILATION ENGINE...   ")
    print("==================================================")
    while True:
        response = cf.describe_change_set(StackName=STACK_NAME, ChangeSetName=SET_NAME)
        status = response['Status']
        print(f"Current Status Matrix Assessment: {status}")
        if status in ['CREATE_COMPLETE', 'FAILED']:
            break
        time.sleep(4)

    if status == 'FAILED':
        print(f"Aborting Change Set Pipeline: {response.get('StatusReason', 'Unknown Error')}")
        return

    print("\n==================================================")
    print(" STEP 3: INFRASTRUCTURE DELTA IMPACT ANALYSIS   ")
    print("==================================================")
    is_safe = True
    for change in response['Changes']:
        resource = change['ResourceChange']
        action = resource['Action']
        res_type = resource['ResourceType']
        logical_id = resource['LogicalResourceId']
        replacement = resource.get('Replacement', 'False')

        print(f"Action:       {action} (Add/Modify/Remove)")
        print(f"Type:         {res_type}")
        print(f"Logical ID:   {logical_id}")
        print(f"Replacement:  {replacement} (True = Destructive Deletion!)")
        print("---")
        
        if replacement == 'True':
            is_safe = False

    print("\n==================================================")
    print(" STEP 4: CONDITIONAL PIPELINE LIFECYCLE DECISION  ")
    print("==================================================")
    if is_safe:
        print("Safety Metrics: PASSED (In-Place Modifications detected). Executing Change Set...")
        cf.execute_change_set(StackName=STACK_NAME, ChangeSetName=SET_NAME)
        print("SUCCESS: Infrastructure migration script running in ap-south-1.")
    else:
        print("CRITICAL ALERT: Destructive Replacement changes detected! Dropping Change Set.")
        cf.delete_change_set(StackName=STACK_NAME, ChangeSetName=SET_NAME)
        print("SUCCESS: Hazardous change set cleanly purged from resource memory logs.")

if __name__ == "__main__":
    execute_pipeline()
