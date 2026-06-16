import boto3
import time
import json

STACK_NAME = 'ml-platform-prod'
cf = boto3.client('cloudformation', region_name='ap-south-1')

def execute_drift_assessment():
    print("==================================================")
    print(" STEP 1: INITIALIZING STACK DRIFT DETECTION ENGINE")
    print("==================================================")
    response = cf.detect_stack_drift(StackName=STACK_NAME)
    drift_detection_id = response['StackDriftDetectionId']
    print(f"Drift Verification Job Dispatched ID: {drift_detection_id}")

    print("\n==================================================")
    print(" STEP 2: WAITING FOR DELTA ALIGNMENT EVALUATION...")
    print("==================================================")
    while True:
        status_response = cf.describe_stack_drift_detection_status(
            StackDriftDetectionId=drift_detection_id
        )
        status = status_response['DetectionStatus']
        print(f"Job Status Assessment: {status}")
        if status in ['DETECTION_COMPLETE', 'DETECTION_FAILED']:
            break
        time.sleep(5)

    if status == 'DETECTION_FAILED':
        print(f"Drift Analysis Aborted: {status_response.get('StatusReason', 'Unknown Error')}")
        return

    print("\n==================================================")
    print(" STEP 3: SCANNING FOR OUT-OF-BAND DRIFTED ASSETS  ")
    print("==================================================")
    # Filter strictly for altered infrastructure components
    drift_details = cf.describe_stack_resource_drifts(
        StackName=STACK_NAME,
        StackResourceDriftStatusFilters=['MODIFIED', 'DELETED']
    )

    drifts = drift_details['StackResourceDrifts']
    if not drifts:
        print("COMPLIANCE VERIFIED: All stack resources match the IaC master template.")
        return

    for drift in drifts:
        print(f"🚨 ALERT: Infrastructure Drift Detected!")
        print(f"  * Resource ID: {drift['LogicalResourceId']}")
        print(f"  * Status:      {drift['StackResourceDriftStatus']} (Bypassed CloudFormation!)")
        
        # Output the exact differences discovered by the delta engine
        if 'PropertyDifferences' in drift:
            for diff in drift['PropertyDifferences']:
                print(f"  * Location:    Property path -> {diff['PropertyPath']}")
                print(f"  * Expected:    {diff['ExpectedValue']} (Template configuration)")
                print(f"  * Actual Live: {diff['ActualValue']} (Console configuration)")
        print("---")

if __name__ == "__main__":
    execute_drift_assessment()
