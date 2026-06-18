import boto3

iam = boto3.client('iam')
ROLE_NAME = 'CodeBuildServiceRole-MLPlatform'

# Modern CodeBuild setups require explicit branch discovery permissions
extra_policy_document = """{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "codecommit:GitPull",
                "codecommit:GetRepository",
                "codecommit:GetBranch",
                "codecommit:GetFolder",
                "codecommit:GetCommit"
            ],
            "Resource": "arn:aws:codecommit:ap-south-1:859977947607:ml-platform"
        }
    ]
}"""

print(f"Injecting explicit CodeCommit pull policies into role: {ROLE_NAME}...")

try:
    # Delete inline policy if it exists from a previous attempt to ensure a clean slate
    iam.delete_role_policy(RoleName=ROLE_NAME, PolicyName='CodeBuildCodeCommitAccess')
except iam.exceptions.NoSuchEntityException:
    pass

# Put the updated inline policy onto the role
iam.put_role_policy(
    RoleName=ROLE_NAME,
    PolicyName='CodeBuildCodeCommitAccess',
    PolicyDocument=extra_policy_document
)

print("Policy attached successfully! Waiting 5 seconds for IAM replication across AWS networks...")
import time; time.sleep(5)
