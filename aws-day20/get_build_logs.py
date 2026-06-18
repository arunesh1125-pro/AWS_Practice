import boto3

codebuild = boto3.client('codebuild', region_name='ap-south-1')
PROJECT_NAME = 'ml-platform-ci'

# Get the latest build execution metadata
builds = codebuild.list_builds_for_project(projectName=PROJECT_NAME, sortOrder='DESCENDING')
latest_build_id = builds['ids'][0] # FIX: Pick the first element from the list string array

print(f"Fetching structural report logs for build target: {latest_build_id}\n")
build_info = codebuild.batch_get_builds(ids=[latest_build_id])['builds'][0] # FIX: Extract index 0 dictionary

# 1. Print Phase Failures
print("--- Execution Phase Breakdown ---")
for phase in build_info.get('phases', []):
    phase_name = phase['phaseType']
    phase_status = phase.get('phaseStatus', 'COMPLETED')
    print(f"Phase: {phase_name:<15} Status: {phase_status}")
    if 'contexts' in phase and phase['phaseStatus'] == 'FAILED':
        print(f"   Reason: {phase['contexts'][0]['message']}") # FIX: Access list wrapper index

# 2. Print any available CloudWatch Log stream indicators
if 'logDetails' in build_info:
    print(f"\nCloudWatch Deep Link: {build_info['logDetails']['deepLink']}")
