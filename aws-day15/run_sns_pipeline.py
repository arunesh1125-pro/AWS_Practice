import json
import boto3

region = "ap-south-1"
sns = boto3.client("sns", region_name=region)
sqs = boto3.client("sqs", region_name=region)
awslambda = boto3.client("lambda", region_name=region)
sts = boto3.client("sts")

account_id = sts.get_caller_identity()["Account"]

# 1. Resolve Target ARNs dynamically
queue_url = sqs.get_queue_url(QueueName="model-events-queue")["QueueUrl"]
queue_arn = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["QueueArn"])["Attributes"]["QueueArn"]
lambda_arn = awslambda.get_function(FunctionName="process-model-event")["Configuration"]["FunctionArn"]

print("Initializing Amazon SNS Topic 'ml-model-events'...")
topic = sns.create_topic(Name="ml-model-events")
topic_arn = topic["TopicArn"]

print("\nConfiguring Fan-out Protocol Pipeline Subscriptions...")
# Change this email to a real address you own to receive notifications
TEST_EMAIL = "arunesh1125@gmail.com" 

# Subscribe Email Endpoints
sns.subscribe(TopicArn=topic_arn, Protocol="email", Endpoint=TEST_EMAIL)
print(f" -> Email tracking sub linked to: {TEST_EMAIL} (Check inbox for confirmation)")

# Subscribe Lambda Function Endpoints
sns.subscribe(TopicArn=topic_arn, Protocol="lambda", Endpoint=lambda_arn)
print(f" -> Lambda tracking sub linked to: {lambda_arn}")

# Subscribe SQS Queue Endpoints
sns.subscribe(TopicArn=topic_arn, Protocol="sqs", Endpoint=queue_arn)
print(f" -> SQS queue tracking sub linked to: {queue_arn}")

# Allow SNS to invoke your Lambda Function
try:
    awslambda.add_permission(
        FunctionName="process-model-event",
        StatementId="AllowSNSToInvoke",
        Action="lambda:InvokeFunction",
        Principal="sns.amazonaws.com",
        SourceArn=topic_arn
    )
except Exception:
    pass

# Allow SNS to send messages to your SQS Queue
sqs_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "sns.amazonaws.com"},
        "Action": "sqs:SendMessage",
        "Resource": queue_arn,
        "Condition": {"ArnEquals": {"aws:SourceArn": topic_arn}}
    }]
}
sqs.set_queue_attributes(QueueUrl=queue_url, Attributes={"Policy": json.dumps(sqs_policy)})


# 2. Publish Message Function Implementation
def publish_model_trained_event(model_id, accuracy, version):
    print(f"\nPublishing event data payload to all pipeline channels...")
    response = sns.publish(
        TopicArn=topic_arn,
        Subject="ML Model Training Complete",
        Message=json.dumps({
            "eventType": "MODEL_TRAINED",
            "modelId": model_id,
            "version": version,
            "accuracy": accuracy,
            "trainedAt": "2026-06-05T23:00:00Z"
        }),
        MessageAttributes={
            "eventType": {"DataType": "String", "StringValue": "MODEL_TRAINED"},
            "accuracy": {"DataType": "String", "StringValue": str(accuracy)} # SQS/SNS attribute type matching constraint fixed
        }
    )
    print(f"✅ Success! Event fan-out completed. MessageId: {response['MessageId']}")

# Execute delivery
publish_model_trained_event(model_id="resnet-v5", accuracy=0.982, version="5.1.0")
