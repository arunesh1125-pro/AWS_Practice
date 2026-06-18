import boto3
from botocore.exceptions import ClientError

# Initialize client
codecommit = boto3.client('codecommit', region_name='ap-south-1')
REPO_NAME = 'ml-platform'

def setup_repository():
    try:
        print(f"Creating repository: {REPO_NAME}...")
        codecommit.create_repository(
            repositoryName=REPO_NAME,
            repositoryDescription='ML Platform source code and pipeline assets'
        )
        print("Repository successfully created.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'RepositoryNameExistsException':
            print(f"Repository '{REPO_NAME}' already exists. Proceeding...")
        else:
            raise e

    # List all active repositories
    print("\n--- Available Repositories ---")
    list_response = codecommit.list_repositories()
    for repo in list_response['repositories']:
        print(f" Active Repo: {repo['repositoryName']}")

    # Gather exact metadata endpoints
    print("\n--- Retrieving Clone URLs ---")
    repo_details = codecommit.get_repository(repositoryName=REPO_NAME)
    metadata = repo_details['repositoryMetadata']
    print(f"HTTPS Endpoint: {metadata['cloneUrlHttp']}")
    print(f"SSH Endpoint:   {metadata['cloneUrlSsh']}")

if __name__ == "__main__":
    setup_repository()
