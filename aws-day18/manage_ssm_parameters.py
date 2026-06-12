import boto3

# Initialize AWS SSM client for Mumbai region
ssm = boto3.client('ssm', region_name='ap-south-1')

# Using your verified working key alias from earlier steps
KEY_ALIAS = 'alias/ml-models-key'

# Global cache for Lambda imitation test
_param_cache = {}

# ── 1. Store parameters ──────────────────────────────────────────────
def store_all_parameters():
    print("==================================================")
    print(" 1. WRITING PARAMETERS TO AWS PARAMETER STORE")
    print("==================================================")
    
    # Plain config value
    print("Writing plain String config value...")
    ssm.put_parameter(
        Name='/ml-platform/production/db-host',
        Value='ml-db.cluster-abc.ap-south-1.rds.amazonaws.com',
        Type='String',
        Description='RDS cluster endpoint for ML platform production',
        Overwrite=True
    )

    # Non-sensitive config list
    print("Writing StringList config array...")
    ssm.put_parameter(
        Name='/ml-platform/production/allowed-model-types',
        Value='xgboost,lightgbm,sklearn,pytorch',
        Type='StringList',
        Overwrite=True
    )

    # Sensitive value — encrypted with KMS
    print(f"Writing SecureString config value encrypted via {KEY_ALIAS}...")
    ssm.put_parameter(
        Name='/ml-platform/production/rds-password',
        Value='S3cur3P@ssw0rd123',
        Type='SecureString',
        KeyId=KEY_ALIAS,
        Description='RDS password — encrypted',
        Overwrite=True
    )
    print("SUCCESS: All parameters written to AWS backend.")

# ── 2. Retrieve parameters patterns ───────────────────────────────────
def demonstrate_retrieval_patterns():
    print("\n==================================================")
    print(" 2. RETRIEVAL PATTERNS DEMONSTRATION")
    print("==================================================")
    
    # Pattern A: Get a single parameter
    response = ssm.get_parameter(Name='/ml-platform/production/db-host')
    print(f"-> Single Fetch (db-host): {response['Parameter']['Value']}")

    # Pattern B: Get SecureString with explicit decryption flag
    response = ssm.get_parameter(Name='/ml-platform/production/rds-password', WithDecryption=True)
    print(f"-> Secure Fetch (rds-password): {response['Parameter']['Value']}")

    # Pattern C: Get multiple parameters at once (Batch)
    response = ssm.get_parameters(
        Names=[
            '/ml-platform/production/db-host',
            '/ml-platform/production/rds-password'
        ],
        WithDecryption=True
    )
    batch_params = {p['Name']: p['Value'] for p in response['Parameters']}
    print(f"-> Batch Fetch Keys Found: {list(batch_params.keys())}")

    # Pattern D: Get all parameters hierarchically by path prefix
    print("-> Fetching all parameters under tree path '/ml-platform/production/'...")
    response = ssm.get_parameters_by_path(
        Path='/ml-platform/production/',
        Recursive=True,
        WithDecryption=True
    )
    all_params = {p['Name']: p['Value'] for p in response['Parameters']}
    for name, value in all_params.items():
        print(f"   * Found: {name} = {value[:15]}...")

# ── 3. Optimized Caching Function ─────────────────────────────────────
def get_config(param_name, with_decryption=False):
    if param_name not in _param_cache:
        print(f"   [Cache Miss] Querying AWS API for: {param_name}")
        response = ssm.get_parameter(Name=param_name, WithDecryption=with_decryption)
        _param_cache[param_name] = response['Parameter']['Value']
    else:
        print(f"   [Cache Hit] Serving from memory for: {param_name}")
    return _param_cache[param_name]

# ── 4. Use in Lambda ──────────────────────────────────────────────────
def lambda_handler(event, context):
    print("\n[Lambda Invocation Lifecycle]")
    db_host  = get_config('/ml-platform/production/db-host')
    password = get_config('/ml-platform/production/rds-password', with_decryption=True)
    model_types = get_config('/ml-platform/production/allowed-model-types')

    return {
        'statusCode': 200,
        'config': {
            'dbHost':      db_host,
            'modelTypes':  model_types.split(',')
        }
    }

# ── Execution Harness ─────────────────────────────────────────────────
if __name__ == "__main__":
    # Step A: Seed parameter values to AWS store
    store_all_parameters()
    
    # Step B: Run advanced bulk/path fetching methods
    demonstrate_retrieval_patterns()
    
    # Step C: First lambda execution (All Cache Misses)
    print("\n--- Running Lambda Invocation 1 ---")
    output_1 = lambda_handler({}, None)
    
    # Step D: Second lambda execution immediately after (All Cache Hits)
    print("\n--- Running Lambda Invocation 2 ---")
    output_2 = lambda_handler({}, None)
    
    print("\n==================================================")
    print(" ALL SSM PARAMETER PATTERNS PASSED SUCCESSFULLY")
    print("==================================================")
