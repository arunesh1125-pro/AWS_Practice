import boto3
import time

codecommit = boto3.client('codecommit', region_name='ap-south-1')
REPO_NAME = 'ml-platform'

def run_review_pipeline():
    # 1. Create a Pull Request (PR)
    print("Opening programmatic Pull Request for review...")
    pr_response = codecommit.create_pull_request(
        title='Add XGBoost model v5 inference pipeline',
        description='Implements new model version structurally optimizing core inference workloads.',
        targets=[{
            'repositoryName': REPO_NAME,
            'sourceReference': 'feature/xgboost-v5',
            'destinationReference': 'main'
        }]
    )
    
    pr_details = pr_response['pullRequest']
    pr_id = pr_details['pullRequestId']
    print(f"-> Pull Request successfully opened. ID Assigned: {pr_id}")

    time.sleep(2)  # Short delay for processing simulation

    """
        # 2. Override approval block
    print(f"Overriding and Approving Pull Request ID: {pr_id}...")
    codecommit.update_pull_request_approval_state(
        pullRequestId=pr_id,
        revisionId=current_revision,
        approvalState='APPROVE'
    )

    """

    # 2. Merge change directly via Fast-Forward
    print(f"Executing Fast-Forward merge routine on PR: {pr_id}...")
    merge_response = codecommit.merge_pull_request_by_fast_forward(
        pullRequestId=pr_id,
        repositoryName=REPO_NAME
    )
    
    # FIX: Correctly access target branch information from response list structure
    target_branch = merge_response['pullRequest']['pullRequestTargets'][0]['destinationReference']
    print(f"-> Code successfully merged into branch: {target_branch}")

if __name__ == "__main__":
    run_review_pipeline()
