import boto3
import json

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
sf_client = boto3.client('stepfunctions', region_name='ap-south-1')
table = dynamodb.Table('PendingTasks')

def simulate_training_completion():
    print("--- Searching for Pending Async Tasks in DynamoDB ---")
    
    # Scan the table to find our active run item
    response = table.scan()
    items = response.get('Items', [])
    
    if not items:
        print("❌ No running jobs found in DynamoDB. Make sure you started the state machine execution first!")
        return

    # Grab the latest running task
    active_task = items[0]
    job_name = active_task['jobName']
    task_token = active_task['taskToken']
    
    print(f"Found active execution entry: {job_name}")
    print("Simulating pipeline success event...")
    
    # Send success response back to Step Functions along with pipeline metrics
    sf_client.send_task_success(
        taskToken=task_token,
        output=json.dumps({
            'accuracy': 0.94, 
            'modelArn': f'arn:aws:s3:::ml-models/{job_name}.tar.gz'
        })
    )
    
    # Clean up the processed tracking entry from DynamoDB
    table.delete_item(Key={'jobName': job_name})
    print(f"✅ Success token dispatched! Step Functions resumed. Cleared {job_name} from DB.")

if __name__ == "__main__":
    simulate_training_completion()
