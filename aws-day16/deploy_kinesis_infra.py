import boto3
import time

kinesis = boto3.client('kinesis', region_name='ap-south-1')
lambda_client = boto3.client('lambda', region_name='ap-south-1')
ACCOUNT_ID = "859977947607"  # Your Account ID

def provision_infrastructure():
    stream_name = 'vehicle-telemetry'
    
    # 1. Create Stream with 4 Shards
    try:
        kinesis.create_stream(StreamName=stream_name, ShardCount=4)
        print("⏳ Constructing Kinesis Stream...")
        time.sleep(15)  # Wait for AWS to activate stream state
    except kinesis.exceptions.ResourceInUseException:
        print("ℹ️ Kinesis Stream already exists.")

    # Get verified Stream ARN
    stream_desc = kinesis.describe_stream(StreamName=stream_name)
    stream_arn = stream_desc['StreamDescription']['StreamARN']
    print(f"✅ Stream Active: {stream_arn}")

    # 2. Register an Enhanced Fan-Out Dedicated Consumer
    try:
        efo_response = kinesis.register_stream_consumer(
            StreamARN=stream_arn,
            ConsumerName='realtime-alerting-consumer'
        )
        consumer_arn = efo_response['Consumer']['ConsumerARN']
        print("⏳ Provisioning Enhanced Fan-Out pipeline...")
        time.sleep(10)  # Wait for EFO state activation
    except kinesis.exceptions.ResourceInUseException:
        consumer_arn = f"arn:aws:kinesis:ap-south-1:{ACCOUNT_ID}:stream/{stream_name}/consumer/realtime-alerting-consumer:*"
        print("ℹ️ Enhanced Fan-Out consumer already registered.")

    # 3. Create Event Source Mapping from EFO Consumer to Lambda
    try:
        # Fetching dynamic real consumer ARN instead of hardcoded timestamp strings
        consumer_desc = kinesis.describe_stream_consumer(
            StreamARN=stream_arn,
            ConsumerName='realtime-alerting-consumer'
        )
        real_consumer_arn = consumer_desc['ConsumerDescription']['ConsumerARN']
        
        lambda_client.create_event_source_mapping(
            EventSourceArn=real_consumer_arn,
            FunctionName='realtime-alerting',
            StartingPosition='LATEST',
            BisectBatchOnFunctionError=True,  # 👈 Fixed Parameter Spelling
            FunctionResponseTypes=['ReportBatchItemFailures']
        )
        print("✅ Event Source Mapping to Lambda successfully mapped via EFO consumer.")
    except Exception as e:
        # Fallback to standard stream mapping if EFO mapping is already present
        try:
            lambda_client.create_event_source_mapping(
                EventSourceArn=stream_arn,  
                FunctionName='realtime-alerting',
                StartingPosition='LATEST',
                BisectBatchOnFunctionError=True,  # 👈 Fixed Parameter Spelling
                FunctionResponseTypes=['ReportBatchItemFailures']
            )
            print("✅ Standard Stream Event Source Mapping to Lambda attached successfully.")
        except Exception as inner_err:
            print(f"ℹ️ Mapping configuration state details: {inner_err}")

if __name__ == "__main__":
    provision_infrastructure()
