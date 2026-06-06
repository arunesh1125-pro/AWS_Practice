import boto3

region = "ap-south-1"
sqs = boto3.client("sqs", region_name=region)

def print_count(queue_name):
    url = sqs.get_queue_url(QueueName=queue_name)["QueueUrl"]
    attrs = sqs.get_queue_attributes(QueueUrl=url, AttributeNames=["ApproximateNumberOfMessages"])
    count = attrs["Attributes"]["ApproximateNumberOfMessages"]
    print(f" -> Queue '{queue_name}' holds: {count} messages.")

print("Current Pipeline Metric Counts:")
print_count("audit-queue")
print_count("deploy-queue")
