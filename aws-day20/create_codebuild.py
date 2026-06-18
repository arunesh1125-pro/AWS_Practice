import boto3

codebuild = boto3.client('codebuild', region_name='ap-south-1')
iam = boto3.client('iam')

# 1. Create a minimal service role for CodeBuild to write logs
ROLE_NAME = 'CodeBuildServiceRole-MLPlatform'
assume_role_policy = """{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "codebuild.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}"""

try:
    print("Creating CodeBuild execution role...")
    role_response = iam.create_role(
        RoleName=ROLE_NAME,
        AssumeRolePolicyDocument=assume_role_policy
    )
    role_arn = role_response['Role']['Arn']
    
    # Attach standard cloud logging permissions
    iam.attach_role_policy(
        RoleName=ROLE_NAME,
        PolicyArn='arn:aws:iam::aws:policy/CloudWatchLogsFullAccess'
    )
    # Allow reading code from CodeCommit
    iam.attach_role_policy(
        RoleName=ROLE_NAME,
        PolicyArn='arn:aws:iam::aws:policy/AWSCodeCommitReadOnly'
    )
    import time; time.sleep(10) # Wait for IAM replication
except iam.exceptions.EntityAlreadyExistsException:
    print("Role already exists. Fetching ARN...")
    role_arn = iam.get_role(RoleName=ROLE_NAME)['Role']['Arn']

# 2. Define and provision CodeBuild project
PROJECT_NAME = 'ml-platform-ci'

try:
    print(f"Provisioning CodeBuild project: {PROJECT_NAME}...")
    codebuild.create_project(
        name=PROJECT_NAME,
        description='Continuous integration testing loop for ML inference layers',
        source={
            'type': 'CODECOMMIT',
            'location': 'https://amazonaws.com'
        },
        artifacts={'type': 'NO_ARTIFACTS'},
        environment={
            'type': 'LINUX_CONTAINER',
            'image': 'aws/codebuild/standard:7.0', # Modern Ubuntu runner environment
            'computeType': 'BUILD_GENERAL1_SMALL'
        },
        serviceRole=role_arn
    )
    print("CodeBuild project successfully registered!")
except codebuild.exceptions.ResourceAlreadyExistsException:
    print("CodeBuild project already exists.")
