import json
import time
import boto3

region = "ap-south-1"
sqs = boto3.client("sqs", region_name=region)

fifo_queue_url = sqs.get_queue_url(QueueName="OrdersQueue.fifo")["QueueUrl"]

def send_order_event(order_id, customer_id, event_type, data, custom_time_epoch=None):
    message_body = json.dumps({
        "orderId": order_id,
        "customerId": customer_id,
        "eventType": event_type,
        "data": data
    })

    # Keep timestamp matching for duplicate testing scenarios
    timestamp = custom_time_epoch if custom_time_epoch else int(time.time())
    dedup_id = f"{order_id}-{event_type}-{timestamp}"

    response = sqs.send_message(
        QueueUrl=fifo_queue_url,
        MessageBody=message_body,
        MessageGroupId=f"order-{order_id}",
        MessageDeduplicationId=dedup_id
    )
    print(f"Sent {event_type} for order {order_id}. SQS MessageId Assigned: {response['MessageId']}")

# --- Simulation Execution Workflow ---
fixed_timestamp = int(time.time())

fixed_timestamp = int(time.time())

print("--- Sending Concurrent Messages (Different Groups -> Processed in Parallel) ---")
send_order_event("o001", "c001", "ORDER_CREATED", {"amount": 99.99}, fixed_timestamp)
send_order_event("o002", "c002", "ORDER_CREATED", {"amount": 49.99}, fixed_timestamp)

print("\n--- Simulating Duplication Submission (Same DedupId -> AWS Deduplication Sweep) ---")
# Re-sending the exact same parameters and fixed_timestamp forces an identical MessageDeduplicationId
send_order_event("o001", "c001", "ORDER_CREATED", {"amount": 99.99}, fixed_timestamp)