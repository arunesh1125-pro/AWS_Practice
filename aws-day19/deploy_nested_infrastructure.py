import boto3
import time
import os

STACK_NAME = 'ml-platform-nested-parent-stack'
BASE_DIR   = r'D:\AWS\aws-day19'

cf  = boto3.client('cloudformation', region_name='ap-south-1')
s3  = boto3.client('s3', region_name='ap-south-1')
sts = boto3.client('sts')

# Automatically pull your live 12-digit AWS Account ID
AWS_ACCOUNT_ID = sts.get_caller_identity()['Account']
S3_BUCKET_NAME = f"{AWS_ACCOUNT_ID}-cf-nested-templates-arunesh"

# Pristine YAML configurations managed using dynamic sub-variables
TEMPLATES = {
    'networking.yaml': (
        "AWSTemplateFormatVersion: '2010-09-09'\n"
        "Description: 'Nested Tier 1: Isolation Networking Fabric'\n"
        "Parameters:\n"
        "  Environment:\n"
        "    Type: String\n"
        "Resources:\n"
        "  DummyVpc:\n"
        "    Type: AWS::EC2::VPC\n"
        "    Properties:\n"
        "      CidrBlock: 10.0.0.0/16\n"
        "      EnableDnsSupport: true\n"
        "      Tags:\n"
        "        - Key: Name\n"
        "          Value: !Sub 'ml-vpc-${Environment}'\n"
        "Outputs:\n"
        "  VpcId:\n"
        "    Value: !Ref DummyVpc\n"
    ),
    'security.yaml': (
        "AWSTemplateFormatVersion: '2010-09-09'\n"
        "Description: 'Nested Tier 2: Access Management and Keys'\n"
        "Parameters:\n"
        "  Environment:\n"
        "    Type: String\n"
        "  VpcId:\n"
        "    Type: String\n"
        "Resources:\n"
        "  NestedKey:\n"
        "    Type: AWS::KMS::Key\n"
        "    Properties:\n"
        "      Description: !Sub 'ML Cryptographic Storage Vault — ${Environment}'\n"
        "      KeyPolicy:\n"
        "        Version: '2012-10-17'\n"
        "        Statement:\n"
        "          - Effect: Allow\n"
        "            Principal:\n"
        "              AWS: !Sub 'arn:aws:iam::${AWS::AccountId}:root'\n"
        "            Action: 'kms:*'\n"
        "            Resource: '*'\n"
        "  NestedRole:\n"
        "    Type: AWS::IAM::Role\n"
        "    Properties:\n"
        "      AssumeRolePolicyDocument:\n"
        "        Version: '2012-10-17'\n"
        "        Statement:\n"
        "          - Effect: Allow\n"
        "            Principal:\n"
        "              Service: 'lambda.amazonaws.com'\n"\
        "            Action: 'sts:AssumeRole'\n"
        "      ManagedPolicyArns:\n"
        "        - 'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'\n"
        "Outputs:\n"
        "  KMSKeyArn:\n"
        "    Value: !GetAtt NestedKey.Arn\n"
        "  LambdaRoleArn:\n"
        "    Value: !GetAtt NestedRole.Arn\n"
    ),
    'application.yaml': (
        "AWSTemplateFormatVersion: '2010-09-09'\n"
        "Description: 'Nested Tier 3: Workload Processing Elements'\n"
        "Parameters:\n"
        "  Environment:\n"
        "    Type: String\n"
        "  VpcId:\n"
        "    Type: String\n"
        "  KMSKeyArn:\n"
        "    Type: String\n"
        "  LambdaRoleArn:\n"
        "    Type: String\n"
        "Resources:\n"
        "  ModelQueue:\n"
        "    Type: AWS::SQS::Queue\n"
        "    Properties:\n"
        "      QueueName: !Sub 'ml-nested-workload-queue-${Environment}'\n"
    ),
    'main-stack.yaml': (
        "AWSTemplateFormatVersion: '2010-09-09'\n"
        "Description: 'ML Platform Root Coordinator Stack'\n"
        "Parameters:\n"
        "  Environment:\n"
        "    Type: String\n"
        "    Default: dev\n"
        "Resources:\n"
        "  NetworkingStack:\n"
        "    Type: AWS::CloudFormation::Stack\n"
        "    Properties:\n"
        "      # FOOLPROOF RESOLUTION: Uses native string interpolation matching your unique bucket folder layout\n"
        "      TemplateURL: " + f"'https://amazonaws.com{S3_BUCKET_NAME}/nested/networking.yaml'\n" +
        "      Parameters:\n"
        "        Environment: !Ref Environment\n"
        "      TimeoutInMinutes: 15\n"\
        "  SecurityStack:\n"\
        "    Type: AWS::CloudFormation::Stack\n"\
        "    DependsOn: NetworkingStack\n"\
        "    Properties:\n"\
        "      TemplateURL: " + f"'https://amazonaws.com{S3_BUCKET_NAME}/nested/security.yaml'\n" +
        "      Parameters:\n"\
        "        Environment: !Ref Environment\n"\
        "        VpcId: !GetAtt NetworkingStack.Outputs.VpcId\n"\
        "  ApplicationStack:\n"\
        "    Type: AWS::CloudFormation::Stack\n"\
        "    DependsOn: [NetworkingStack, SecurityStack]\n"\
        "    Properties:\n"\
        "      TemplateURL: " + f"'https://amazonaws.com{S3_BUCKET_NAME}/nested/application.yaml'\n" +
        "      Parameters:\n"
        "        Environment: !Ref Environment\n"\
        "        VpcId: !GetAtt NetworkingStack.Outputs.VpcId\n"\
        "        KMSKeyArn: !GetAtt SecurityStack.Outputs.KMSKeyArn\n"\
        "        LambdaRoleArn: !GetAtt SecurityStack.Outputs.LambdaRoleArn\n"
    )
}

def setup_and_launch():
    print(f"Detected Live AWS Context Account ID: {AWS_ACCOUNT_ID}")
    print("Step 0: Clearing legacy caching stacks with robust active wait monitoring...")
    try:
        cf.delete_stack(StackName=STACK_NAME)
        waiter = cf.get_waiter('stack_delete_complete')
        waiter.wait(StackName=STACK_NAME, WaiterConfig={'Delay': 5, 'MaxAttempts': 30})
        print("  * Wipe completed successfully. Ready for clean deployment.")
    except Exception:
        pass

    print("Step 1: Instantiating globally unique template registry bucket...")
    try:
        s3.create_bucket(
            Bucket=S3_BUCKET_NAME,
            CreateBucketConfiguration={'LocationConstraint': 'ap-south-1'}
        )
        print(f"  * Created bucket: s3://{S3_BUCKET_NAME}")
    except Exception:
        print(f"  * Bucket s3://{S3_BUCKET_NAME} ready.")

    print("Step 2: Overwriting layout template sheets to local disk folder...")
    os.makedirs(BASE_DIR, exist_ok=True)
    for name, content in TEMPLATES.items():
        with open(os.path.join(BASE_DIR, name), 'w') as f:
            f.write(content)

    print("\nStep 3: Syncing child templates to secure cloud registry...")
    child_templates = ['networking.yaml', 'security.yaml', 'application.yaml']
    for file_name in child_templates:
        local_path = os.path.join(BASE_DIR, file_name)
        s3.upload_file(local_path, S3_BUCKET_NAME, f"nested/{file_name}")
        print(f"  * Uploaded {file_name} -> s3://{S3_BUCKET_NAME}/nested/{file_name}")

    print("\nStep 4: Dispatching creation signal to CloudFormation root orchestrator...")
    with open(os.path.join(BASE_DIR, 'main-stack.yaml'), 'r') as f:
        root_template_body = f.read()

    cf.create_stack(
        StackName=STACK_NAME,
        TemplateBody=root_template_body,
        Parameters=[{'ParameterKey': 'Environment', 'ParameterValue': 'dev'}],
        Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM']
    )
    print(f"Deployment process successfully initiated for: '{STACK_NAME}'")

    print("\nStep 5: Tracking real-time nested allocation status logs...")
    while True:
        try:
            resp = cf.describe_stacks(StackName=STACK_NAME)
            status = resp['Stacks'][0]['StackStatus']
            print(f"Current Architecture Sync Status: {status}")
            if status in ['CREATE_COMPLETE', 'ROLLBACK_COMPLETE', 'CREATE_FAILED']:
                break
        except Exception:
            print("Waiting for stack initialization layer to sync...")
        time.sleep(15)

    if status == 'CREATE_COMPLETE':
        print("\n==================================================")
        print(" SUCCESS: MULTI-TIER NESTED INFRASTRUCTURE DEPLOYED")
        print("==================================================")
    else:
        print(f"\n🚨 DEPLOYMENT FAILED: Status is {status}. Pulling exact AWS error logs...")
        events = cf.describe_stack_events(StackName=STACK_NAME)['StackEvents']
        print("\n--- DETAILED FAILURE EVENTS ---")
        for event in events:
            if event['ResourceStatus'] in ['CREATE_FAILED', 'ROLLBACK_IN_PROGRESS']:
                print(f"Resource: {event['LogicalResourceId']}")
                print(f"Status:   {event['ResourceStatus']}")
                print(f"Reason:   {event.get('ResourceStatusReason', 'N/A')}")
                print("-" * 30)

if __name__ == "__main__":
    setup_and_launch()
