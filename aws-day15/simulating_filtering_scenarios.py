import json
import boto3

region = "ap-south-1"
sns = boto3.client("sns", region_name=region)
sqs = boto3.client("sqs", region_name=region)

topic_arn = sns.create_topic(Name="ml-model-events")["TopicArn"]

def dispatch_event(subject, body_dict, attr_dict):
    print(f"\nPublishing Event: {subject}...")
    # Convert pure float values into string form for SQS/SNS attribute schema mapping compatibility
    formatted_attrs = {}
    for k, v in attr_dict.items():
        if isinstance(v, (int, float)):
            formatted_attrs[k] = {"DataType": "Number", "StringValue": str(v)}
        else:
            formatted_attrs[k] = {"DataType": "String", "StringValue": str(v)}

    sns.publish(
        TopicArn=topic_arn,
        Subject=subject,
        Message=json.dumps(body_dict),
        MessageAttributes=formatted_attrs
    )

# Scenario 1: Low Accuracy (Should skip deployment engine filter)
dispatch_event(
    subject="Low Accuracy Model Alert",
    body_dict={"modelId": "vgg16", "status": "TRAINED"},
    attr_dict={"eventType": "MODEL_TRAINED", "accuracy": 0.74}
)

# Scenario 2: High Accuracy (Should trigger deployment pipeline engine)
dispatch_event(
    subject="High Accuracy Model Alert",
    body_dict={"modelId": "resnet101", "status": "READY_FOR_PROD"},
    attr_dict={"eventType": "MODEL_TRAINED", "accuracy": 0.94}
)

# Scenario 3: Execution Runtime Crash (Should isolate directly to Lambda monitoring team)
dispatch_event(
    subject="Pipeline Crash Alert",
    body_dict={"modelId": "bert-base", "error": "Out Of Memory Exception"},
    attr_dict={"eventType": "MODEL_FAILED"}
)

print("\nAll simulated messages dispatched. Processing queue tally check follows...")
