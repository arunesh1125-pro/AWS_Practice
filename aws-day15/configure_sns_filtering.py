import json
import boto3

region = "ap-south-1"
sns = boto3.client("sns", region_name=region)
sqs = boto3.client("sqs", region_name=region)
awslambda = boto3.client("lambda", region_name=region)

# 1. Fetch resource assets
topic_arn = sns.create_topic(Name="ml-model-events")["TopicArn"]
audit_url = sqs.get_queue_url(QueueName="audit-queue")["QueueUrl"]
audit_arn = sqs.get_queue_attributes(QueueUrl=audit_url, AttributeNames=["QueueArn"])["Attributes"]["QueueArn"]
deploy_url = sqs.get_queue_url(QueueName="deploy-queue")["QueueUrl"]
deploy_arn = sqs.get_queue_attributes(QueueUrl=deploy_url, AttributeNames=["QueueArn"])["Attributes"]["QueueArn"]
lambda_arn = awslambda.get_function(FunctionName="alert-on-failure")["Configuration"]["FunctionArn"]

print("Configuring Fan-out Filter Policies across system components...")

# Subscriber A: SQS Audit Queue (No Filter - Receives All)
sns.subscribe(TopicArn=topic_arn, Protocol="sqs", Endpoint=audit_arn)

# Subscriber B: SQS Deploy Queue (Only highly accurate trained models)
deploy_policy = {
    "eventType": ["MODEL_TRAINED"],
    "accuracy": [{"numeric": [">=", 0.90]}]
}
sns.subscribe(
    TopicArn=topic_arn,
    Protocol="sqs",
    Endpoint=deploy_arn,
    Attributes={"FilterPolicy": json.dumps(deploy_policy)}
)

# Subscriber C: Lambda Failure Monitor (Only processing failures)
lambda_policy = {
    "eventType": ["MODEL_FAILED", "PREDICTION_ERROR"]
}
sns.subscribe(
    TopicArn=topic_arn,
    Protocol="lambda",
    Endpoint=lambda_arn,
    Attributes={"FilterPolicy": json.dumps(lambda_policy)}
)

# 2. Grant structural permissions
try:
    awslambda.add_permission(
        FunctionName="alert-on-failure", 
        StatementId="SNSInvoke", 
        Action="lambda:InvokeFunction", 
        Principal="sns.amazonaws.com",  # FIXED: Changed from placeholder to sns
        SourceArn=topic_arn
    )
except Exception: 
    pass

def allow_sqs(url, arn):
    # FIXED: Changed principal service dictionary mapping to sns.amazonaws.com
    p = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "sns.amazonaws.com"}, 
            "Action": "sqs:SendMessage",
            "Resource": arn,
            "Condition": {"ArnEquals": {"aws:SourceArn": topic_arn}}
        }]
    }
    sqs.set_queue_attributes(QueueUrl=url, Attributes={"Policy": json.dumps(p)})

allow_sqs(audit_url, audit_arn)
allow_sqs(deploy_url, deploy_arn)
print("✅ Subscriptions successfully established with live filtering parameters.")
