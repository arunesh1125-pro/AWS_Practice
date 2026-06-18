import boto3
import time

# Explicitly bind the client to your Mumbai region
codebuild = boto3.client('codebuild', region_name='ap-south-1')
PROJECT_NAME = 'ml-platform-ci'

print(f"Triggering continuous integration run for project: {PROJECT_NAME}...")

# FIX: Explicitly passing sourceVersion pointing to our main branch
start_response = codebuild.start_build(
    projectName=PROJECT_NAME,
    sourceVersion='refs/heads/main' 
)
build_id = start_response['build']['id']

print(f"Build initialized. Tracking active run status for ID: {build_id}\n")

while True:
    info = codebuild.batch_get_builds(ids=[build_id])
    status = info['builds'][0]['buildStatus']
    print(f"Current Execution Status: {status}")
    
    if status in ['SUCCEEDED', 'FAILED', 'FAULT', 'TIMED_OUT', 'STOPPED']:
        print(f"\nFinal Execution Phase State Resolved As: {status}")
        break
        
    time.sleep(15)
