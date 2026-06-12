import boto3
import json
import time
from botocore.exceptions import ClientError

# Initialize Secrets Manager client for Mumbai region
sm = boto3.client('secretsmanager', region_name='ap-south-1')

# Using your verified working key alias from earlier steps
KEY_ALIAS = 'alias/ml-models-key'
SECRET_NAME = 'ml-platform/production/rds-credentials'

# Global cache for Lambda imitation test
_secret_cache = {}
_cache_ttl    = 300    # refresh every 5 minutes

# ── 1. Create a secret ──────────────────────────────────────────────
def create_database_secret():
    secret_value = {
        'username': 'ml_admin',
        'password': 'InitialP@ssw0rd123',
        'host':     'ml-db.cluster-abc.ap-south-1.rds.amazonaws.com',
        'port':     5432,
        'dbname':   'mlplatform'
    }

    try:
        print(f"Creating secret '{SECRET_NAME}' encrypted with '{KEY_ALIAS}'...")
        response = sm.create_secret(
            Name=SECRET_NAME,
            Description='RDS PostgreSQL credentials for ML platform production',
            SecretString=json.dumps(secret_value),
            KmsKeyId=KEY_ALIAS
        )
        print(f"SUCCESS: Secret Created! ARN: {response['ARN']}")
    except sm.exceptions.ResourceExistsException:
        print(f"INFO: Secret '{SECRET_NAME}' already exists. Skipping creation step.")

# ── 2. Retrieve a secret with caching ─────────────────────────────
def get_secret(secret_name):
    now = time.time()

    # Return cached value if fresh
    if secret_name in _secret_cache:
        cached_value, cached_time = _secret_cache[secret_name]
        if now - cached_time < _cache_ttl:
            print("-> [Cache Hit] Returning credentials from memory cache.")
            return cached_value

    # Cache miss or expired — fetch from Secrets Manager
    print("-> [Cache Miss] Fetching fresh credentials from AWS Secrets Manager...")
    try:
        response = sm.get_secret_value(SecretId=secret_name)

        if 'SecretString' in response:
            secret = json.loads(response['SecretString'])
        else:
            import base64
            secret = json.loads(base64.b64decode(response['SecretBinary']))

        # Cache the result
        _secret_cache[secret_name] = (secret, now)
        return secret

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceNotFoundException':
            print(f"Secret {secret_name} not found")
        elif error_code == 'AccessDeniedException':
            print(f"No permission to access {secret_name}")
        raise

# ── 3. Update a secret manually ──────────────────────────────────────
def update_database_secret():
    updated_value = {
        'username': 'ml_admin',
        'password': 'NewS3cur3P@ssw0rd456',
        'host':     'ml-db.cluster-abc.ap-south-1.rds.amazonaws.com',
        'port':     5432,
        'dbname':   'mlplatform'
    }
    print(f"\nUpdating secret payload with a new password...")
    sm.put_secret_value(
        SecretId=SECRET_NAME,
        SecretString=json.dumps(updated_value)
    )
    print("SUCCESS: Secret payload updated.")

# ── 4. Use in Lambda handler (Simulated execution block) ───────────
def lambda_handler(event, context):
    print("\nExecuting lambda_handler event lifecycle loop...")
    creds = get_secret(SECRET_NAME)
    
    # Mocking DB connection here so script runs without installing psycopg2 or stalling on fake URL
    print(f"Simulating connection to database server: {creds['host']}")
    print(f"Authenticated as user: '{creds['username']}' with password string length: {len(creds['password'])}")
    
    mock_count = 42  # fake model runs count
    return {'statusCode': 200, 'modelRunCount': mock_count}

# ── Test Lifecycle Pipeline ─────────────────────────────────────────
if __name__ == "__main__":
    print("==================================================")
    print(" SECRETS MANAGER OPERATIONS LIFECYCLE RUNNER")
    print("==================================================")
    
    # 1. Create the secret instance
    create_database_secret()
    
    # 2. First call: Cache Miss (calls AWS API)
    result_1 = lambda_handler({}, None)
    
    # 3. Second call immediately after: Cache Hit (saves API overhead cost)
    result_2 = lambda_handler({}, None)
    
    # 4. Update password to simulate password rotation
    update_database_secret()
    
    # 5. Evict cache manually to force discovery of new password
    _secret_cache.clear()
    result_3 = lambda_handler({}, None)
    
    print("\n==================================================")
    print(" PIPELINE COMPLETED CLEANLY WITH VERIFIED CACHING")
    print("==================================================")
