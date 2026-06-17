import boto3
import time
import json

STACK_NAME = 'sam-hands-on-processor-stack'

# Region is globally bound right here
cf = boto3.client('cloudformation', region_name='ap-south-1')

SAM_TEMPLATE = """AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: 'Minimal Verified SAM Workload Engine'

Parameters:
  Environment:
    Type: String
    Default: dev

Resources:
  PredictionsTable:
    Type: AWS::Serverless::SimpleTable
    Properties:
      TableName: !Sub 'predictions-store-${Environment}'

  MLInferenceFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub 'sam-inference-engine-${Environment}'
      Runtime: python3.12
      Handler: index.handler
      InlineCode: |
        import json
        def handler(event, context):
            return {
                "statusCode": 200,
                "body": json.dumps({"status": "SAM Stack Active!"})
            }
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref PredictionsTable
"""

def execute_sam_deployment():
    print("==================================================")
    print(" CLEANING PREVIOUS IDENTICAL WORKING HOOKS        ")
    print("==================================================")
    try:
        cf.delete_stack(StackName=STACK_NAME)
        waiter = cf.get_waiter('stack_delete_complete')
        waiter.wait(StackName=STACK_NAME, WaiterConfig={'Delay': 5, 'MaxAttempts': 30})
        print("  * System cache cleared. Proceeding to launch...")
    except Exception:
        pass

    print("\n==================================================")
    print(" DISPATCHING DEPLOYMENT TO AWS SAM ENGINE          ")
    print("==================================================")
    
    cf.create_stack(
        StackName=STACK_NAME,
        TemplateBody=SAM_TEMPLATE,
        Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND'] # FIX: Removed invalid RegionName parameter
    )
    print("Serverless application pipeline initialized successfully.")

    print("\n==================================================")
    print(" TRACKING LIVE ARCHITECTURE BUILD PROGRESS         ")
    print("==================================================")
    while True:
        try:
            resp = cf.describe_stacks(StackName=STACK_NAME)
            status = resp['Stacks'][0]['StackStatus'] # FIX: Accessing correct list dictionary index
            print(f"Current Architecture Generation Phase: {status}")
            if status in ['CREATE_COMPLETE', 'ROLLBACK_COMPLETE', 'CREATE_FAILED']:
                break
        except Exception:
            print("Syncing tracking identifiers with ap-south-1 console...")
        time.sleep(10)

    if status == 'CREATE_COMPLETE':
        print("\n==================================================")
        print(" 🎉 SUCCESS: SAM TEMPLATE TRANSLATED AND DEPLOYED")
        print("==================================================")
        print("Go check your AWS Management Console for:")
        print(" 1. DynamoDB -> predictions-store-dev")
        print(" 2. Lambda    -> sam-inference-engine-dev")
    else:
        print(f"\nDeployment stopped. Check your console. Status: {status}")

if __name__ == "__main__":
    execute_sam_deployment()
