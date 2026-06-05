import time
import boto3

region = "ap-south-1"
sqs = boto3.client("sqs", region_name=region)

main_queue_url = sqs.get_queue_url(QueueName="ml-jobs")["QueueUrl"]
dlq_url = sqs.get_queue_url(QueueName="ml-jobs-dlq")["QueueUrl"]

print("Simulating arrival of an error-causing task payload...")
sqs.send_message(QueueUrl=main_queue_url, MessageBody="Corrupt ML Model Weights Payload #404")

print("\nSimulating Worker pulling and breaking on the message 3 times...")
for attempt in range(1, 4):
    print(f" -> Consumer Poll Attempt #{attempt}")
    response = sqs.receive_message(QueueUrl=main_queue_url, MaxNumberOfMessages=1, VisibilityTimeout=2)
    messages = response.get("Messages", [])
    if messages:
        print("    Processing failed. Dropping connection to force recovery retry loop...")
        time.sleep(2.5)  # Sleep past visibility timeout so it reappears

print("\nVerifying DLQ interception rule...")
# Poll main queue again; it should be empty now
empty_check = sqs.receive_message(QueueUrl=main_queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=1)
if "Messages" not in empty_check:
    print(" -> Main Queue is empty. Message was successfully banished to DLQ!")

# --- Step 4: Replay Function ---
def replay_from_dlq(max_messages=100):
    print("\n--- Initializing Automated DLQ Recovery Replay Mechanism ---")
    replayed = 0
    while replayed < max_messages:
        response = sqs.receive_message(QueueUrl=dlq_url, MaxNumberOfMessages=10)
        messages = response.get("Messages", [])
        if not messages:
            break

        for msg in messages:
            print(f" -> Replaying message body: '{msg['Body']}' back to processing pipeline.")
            sqs.send_message(QueueUrl=main_queue_url, MessageBody=msg["Body"])
            sqs.delete_message(QueueUrl=dlq_url, ReceiptHandle=msg["ReceiptHandle"])
            replayed += 1

    print(f"Replayed {replayed} messages from DLQ")
    return replayed

# Execute replay action
replay_from_dlq()
