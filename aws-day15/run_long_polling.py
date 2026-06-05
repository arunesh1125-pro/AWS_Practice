import time
import boto3

region = "ap-south-1"
sqs = boto3.client("sqs", region_name=region)

# Dynamically resolve your real queue URL address mapping
QUEUE_URL = sqs.get_queue_url(QueueName="production-workload-queue")["QueueUrl"]

# --- Method 1: Long Polling applied directly to the individual API call ---
print("\n--- Method 1: Running API-Level Long Polling Request ---")
print("Polling empty queue... This will hold open and wait for 20 seconds...")

start_time = time.time()
response = sqs.receive_message(
    QueueUrl=QUEUE_URL,
    MaxNumberOfMessages=10,
    WaitTimeSeconds=20,     # Explicit long polling connection hold (1-20s allowed) [1]
    VisibilityTimeout=60
)
duration = time.time() - start_time
print(f"Connection closed after {duration:.2f} seconds.")
print(f"Messages fetched: {len(response.get('Messages', []))}")


# --- Method 2: Configure Long Polling globally at the Queue level ---
print("\n--- Method 2: Configuring Long Polling permanently at Queue infrastructure level ---")
sqs.set_queue_attributes(
    QueueUrl=QUEUE_URL,
    Attributes={
        'ReceiveMessageWaitTimeSeconds': '20'   # Enforces a global 20s long-polling baseline [1]
    }
)
print("✅ Success: Queue attributes updated. All future consumers use long polling automatically! [1]")


# --- Verification: Calling receive_message without specifying parameters ---
print("\n--- Verification: Testing default call on the updated queue configuration ---")
print("Polling again without passing explicitly defined WaitTimeSeconds parameters...")

start_time = time.time()
# No WaitTimeSeconds passed here, but it will still wait 20s due to our queue attribute update [1]
response_default = sqs.receive_message(
    QueueUrl=QUEUE_URL,
    MaxNumberOfMessages=10,
    VisibilityTimeout=60
)
duration_default = time.time() - start_time
print(f"Connection closed after {duration_default:.2f} seconds.")
print(f"Messages fetched: {len(response_default.get('Messages', []))}")
