import boto3
import json

lambda_client = boto3.client('lambda', region_name='ap-south-1')

# SYNCHRONOUS invovation
# Caller blocker until Lambda Returns (Request Response)
response = lambda_client.invoke(
    FunctionName='my-processing-function1',
    InvocationType='RequestResponse',
    Payload=json.dumps({"user_id": "u123", "action": "predict" })
)

result = json.loads(response['Payload'].read())
print(result)   # you get the actual return value

# ASYNCRONOUS invocation
# Caller gets 202 immediately, Lambda runs in background  (Event)
response = lambda_client.invoke(
    FunctionName='my-processing-function1',
    InvocationType='Event',
    Payload=json.dumps({"user_id": "u456", "action": "retrain" })
)

print(response['StatusCode']) # 202 - accepted, not completed
# You do NOT get the return value here