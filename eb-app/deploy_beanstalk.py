import boto3
import time
import os

APPLICATION_NAME = 'ml-inference-platform'
ENVIRONMENT_NAME = 'mlinferenceplatform-env'
ZIP_FILE_PATH    = r'D:\AWS\eb-app\deployment-package.zip'

TIMESTAMP     = time.strftime("%Y%m%d-%H%M%S")
VERSION_LABEL = f"v1.0.0-{TIMESTAMP}"

eb = boto3.client('elasticbeanstalk', region_name='ap-south-1')
s3 = boto3.client('s3', region_name='ap-south-1')

def get_latest_python_platform_arn():
    print("Querying AWS for the latest valid Python 3.12 Platform branch...")
    # Dynamically look up active platform versions matching Python 3.12 on AL2023
    platforms = eb.list_platform_versions(
        Filters=[
            {'Type': 'PlatformName', 'Operator': '=', 'Values': ['Python 3.12 running on 64bit Amazon Linux 2023']},
            {'Type': 'PlatformStatus', 'Operator': '=', 'Values': ['Ready']}
        ]
    )
    if not platforms.get('PlatformSummaryList'):
        raise RuntimeError("Could not find a valid active Python 3.12 Platform branch in this region.")
    
    # Grab the newest available platform version entry
    latest_arn = platforms['PlatformSummaryList'][0]['PlatformArn']
    print(f"  * Discovered Valid Production ARN: {latest_arn}")
    return latest_arn

def run_deployment():
    print(f"Generated Unique Version Label: '{VERSION_LABEL}'")
    
    # 1. Fetch latest active platform configuration
    platform_arn = get_latest_python_platform_arn()

    # 2. Fetch storage vault location
    print("Step 1: Fetching Elastic Beanstalk storage vault...")
    response = eb.create_storage_location()
    s3_bucket = response['S3Bucket']
    s3_key = f"{APPLICATION_NAME}/{VERSION_LABEL}.zip"

    # 3. Upload package archive
    print(f"Step 2: Uploading package artifact to s3://{s3_bucket}/{s3_key}...")
    s3.upload_file(ZIP_FILE_PATH, s3_bucket, s3_key)

    # 4. Register application version label
    print(f"Step 3: Creating application version registration hook using unique tag: '{VERSION_LABEL}'...")
    eb.create_application_version(
        ApplicationName=APPLICATION_NAME,
        VersionLabel=VERSION_LABEL,
        SourceBundle={'S3Bucket': s3_bucket, 'S3Key': s3_key},
        AutoCreateApplication=True
    )

    # 5. Handle creation fallback using the dynamic platform tracker hook
    try:
        print(f"Step 4: Attempting to update environment context cluster...")
        eb.update_environment(
            EnvironmentName=ENVIRONMENT_NAME,
            VersionLabel=VERSION_LABEL
        )
        print("SUCCESS: Existing environment update operation issued successfully.")
    except Exception as e:
        error_msg = str(e)
        if "No Environment found" in error_msg or "ResourceNotFound" in error_msg:
            print(f"Step 4b: Confirmed environment is missing. Launching a fresh environment host: '{ENVIRONMENT_NAME}'...")
            eb.create_environment(
                ApplicationName=APPLICATION_NAME,
                EnvironmentName=ENVIRONMENT_NAME,
                VersionLabel=VERSION_LABEL,
                PlatformArn=platform_arn # FIX: Now passes the dynamic verified version ARN
            )
            print("SUCCESS: New infrastructure pipeline allocation initialized successfully.")
        else:
            raise e

if __name__ == "__main__":
    if not os.path.exists(ZIP_FILE_PATH):
        print(f"Error: Missing code archive. Rebuild target asset at: {ZIP_FILE_PATH}")
    else:
        run_deployment()
