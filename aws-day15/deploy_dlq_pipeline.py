import json
import boto3
from botocore.exceptions import ClientError

region = "ap-south-1"
sqs = boto3.client("sqs", region_name=region)
cloudwatch = boto3.client("cloudwatch", region_name=region)

# PASTE YOUR REAL SNS ARN FROM STEP 1 HERE:
SNS_ALERT_ARN = "arn:aws:sns:ap-south-1:859977947607:ops-alerts" 

print("Step 1: Provisioning Dead Letter Queue 'ml-jobs-dlq'...")
dlq_response = sqs.create_queue(
    QueueName="ml-jobs-dlq",
    Attributes={"MessageRetentionPeriod": "1209600"}  # 14 days retention
)
dlq_url = dlq_response["QueueUrl"]

dlq_arn = sqs.get_queue_attributes(
    QueueUrl=dlq_url, AttributeNames=["QueueArn"]
)["Attributes"]["QueueArn"]

print("Step 2: Provisioning Main Queue 'ml-jobs' linked to DLQ...")
try:
    main_queue_response = sqs.create_queue(
        QueueName="ml-jobs",
        Attributes={
            "VisibilityTimeout": "5",  # Short timeout for quick simulation testing
            "RedrivePolicy": json.dumps({
                "deadLetterTargetArn": dlq_arn,
                "maxReceiveCount": "3"  # After 3 failures -> automatically routes to DLQ
            })
        }
    )
    main_queue_url = main_queue_response["QueueUrl"]
except ClientError as e:
    # If queue already exists, resolve URL manually
    main_queue_url = sqs.get_queue_url(QueueName="ml-jobs")["QueueUrl"]

print("Step 3: Configuring CloudWatch Alarm monitoring system...")
cloudwatch.put_metric_alarm(
    AlarmName="MLJobsDLQNotEmpty",
    MetricName="ApproximateNumberOfMessagesVisible",
    Namespace="AWS/SQS",
    Dimensions=[{"Name": "QueueName", "Value": "ml-jobs-dlq"}],
    Statistic="Sum",
    Period=60,
    EvaluationPeriods=1,
    Threshold=1.0,
    ComparisonOperator="GreaterThanOrEqualToThreshold",
    AlarmActions=[SNS_ALERT_ARN]
)

print(f"✅ Infrastructure Live!\nMain URL: {main_queue_url}\nDLQ URL: {dlq_url}")
