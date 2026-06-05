import json
import sys
import boto3

region = "ap-south-1"
sqs = boto3.client("sqs", region_name=region)

try:
    QUEUE_URL = sqs.get_queue_url(QueueName="ml-jobs")["QueueUrl"]
except Exception as e:
    print(f"Error fetching queue URL. Did you create it? Details: {e}")
    sys.exit(1)

def run_ml_job(body):
    print(f" -> Execution Engine: Analyzing Job ID '{body.get('jobId')}' with model '{body.get('model')}'...")
    if body.get("status") == "CORRUPT":
        raise ValueError("Simulated Runtime Error: Model configuration weights are corrupted!")
    print(f" -> Execution Engine: Job ID '{body.get('jobId')}' finalized successfully.")

def consume_message():
    print("\nPolling queue for available workloads (Up to 20s long-polling wait)...")
    response = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=1,
        VisibilityTimeout=120,  # Hidden for 2 minutes from other consumers
        WaitTimeSeconds=20      # Long Polling wrapper connection wait
    )

    messages = response.get("Messages", [])
    if not messages:
        print("No workloads currently available in queue.")
        return False

    message = messages[0]
    receipt_handle = message["ReceiptHandle"]

    try:
        body = json.loads(message["Body"])
        run_ml_job(body)

        # Success path: Delete from queue immediately
        sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=receipt_handle)
        print("✅ SUCCESS: Message processed and safely purged from queue.")

    except Exception as e:
        print(f"❌ FAILURE: Processing failed: {e}")
        print(" -> Action: Extending Visibility Timeout to 300 seconds for isolation triage...")
        
        # Error path: Keep hidden longer to analyze error states before reprocessing
        sqs.change_message_visibility(
            QueueUrl=QUEUE_URL,
            ReceiptHandle=receipt_handle,
            VisibilityTimeout=300
        )
    return True

if __name__ == "__main__":
    print("--- Processing Task 1 (Expected Success Pass) ---")
    consume_message()

    print("\n--- Processing Task 2 (Expected Failure Triage Pass) ---")
    consume_message()
