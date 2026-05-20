import json
import boto3
import os
from decimal import Decimal

# intialize clients OUTSIDE the handler
# This code runs once during cold start
# On warm invocations it's reused — saves 200–500ms per call

s3_client  = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

BUCKET = os.environ['CONFIG_BUCKET']
TABLE = os.environ['RESULTS_TABLE']

def lambda_handler(event, context):
    """
    Trigger by: API Gateway POST /process
    Input:  {"job_id": "j001", "config_key": "configs/job.json"}
    Output: {"statusCode": 200, "body": {"status": "ok"}}
    """
    job_id = event.get('job_id')
    config_key = event.get('config_key')

    if not job_id or not config_key:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "job_id and config_keys required"})
        }
    
    try:
        # Step 1: Read config from S3
        response = s3_client.get_object(Bucket=BUCKET, Key=config_key)
        config = json.loads(response['Body'].read().decode('utf-8'))
        print(f"Loaded config for job {job_id}: {config}")

        # Step 2: Process (your ML logic here)
        result = {
            "job_id": job_id,
            "model": config.get("model_name", "default"),
            "accuracy": Decimal(str(config.get("threshold", 0.85))),
            "status": "completed"
        }

        # Step 3: Save result to DynamoDB
        table = dynamodb.Table(TABLE)
        table.put_item(Item=result)
        print(f"Saved: {result}")

        return {
            "statusCode": 200,
            "body": json.dumps({"status": "ok", "job_id": job_id})
        }
    
    except s3_client.exceptions.NoSuchKey:
        print(f"Config not found: s3://{BUCKET}/{config_key}")
        return {
            "statusCode": 404,
            "body": json.dumps({"error": f"Config {config_key} not found"})
        }
    
    except Exception as e:
        print(f"Unhandled error: {str(e)}")
        raise  # re-raise -> triggers async retry + DLQ
