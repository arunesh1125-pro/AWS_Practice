import boto3

codebuild = boto3.client('codebuild', region_name='ap-south-1')
PROJECT_NAME = 'ml-platform-ci'

print(f"Updating source location configuration for {PROJECT_NAME}...")

codebuild.update_project(
    name=PROJECT_NAME,
    source={
        'type': 'CODECOMMIT',
        'location': 'ml-platform'  # <-- FIX: Changed from URL to raw repository name
    }
)

print("CodeBuild project configuration successfully corrected!")
