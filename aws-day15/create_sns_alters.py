import boto3

region = "ap-south-1"
sns = boto3.client("sns", region_name=region)

print("Creating Amazon SNS topic for operational alerts...")
response = sns.create_topic(Name="ops-alerts")
sns_arn = response["TopicArn"]

print(f"✅ Success! Use this real SNS ARN in your scripts: {sns_arn}")
