import boto3
import json

# Initialize structural resources
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')

# Mocking the JWT validation step locally since we are testing token processing logic 
def mock_decode_and_validate_jwt(token):
    print("-> Mock-decoding JWT bearer token signature payload...")
    # This matches the schema that our Pre-Token function generates
    return {
        'sub': 'usr-859977947607',
        'email': 'ml_engineer_test@example.com',
        'subscription_plan': 'enterprise',
        'max_api_calls': '5000',
        'tenant_id': 'tenant-omega-9'
    }

def mock_is_rate_limited(user_id, max_calls):
    return False

def generate_policy(principal_id, effect, method_arn):
    return {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                'Resource': method_arn
            }]
        }
    }

# ── 1. Cognito Pre Token Generation Trigger ──────────────────────────
def pre_token_generation_trigger(event, context):
    """
    Invoked automatically by AWS Cognito immediately before token issuance.
    """
    user_id  = event['userName']
    print(f"\n[Cognito Trigger] Processing token claims generation for user: {user_id}")

    # Fetch user's active subscription tier configurations from DynamoDB
    try:
        table    = dynamodb.Table('UserSubscriptions')
        response = table.get_item(Key={'userId': user_id})
        user     = response.get('Item', {})
        print(f"-> DB Metadata Found: Plan={user.get('plan')}, Limit={user.get('apiLimit')}")
    except Exception as db_err:
        print(f"-> Database Lookup Failed: {db_err}. Defaulting to fallback parameters.")
        user = {}

    # Mutate event payload to inject custom claims directly into output JWT structure
    event['response']['claimsOverrideDetails'] = {
        'claimsToAddOrOverride': {
            'subscription_plan': str(user.get('plan', 'free')),
            'max_api_calls':     str(user.get('apiLimit', 100)),
            'tenant_id':         str(user.get('tenantId', 'default'))
        }
    }
    return event

# ── 2. API Gateway Custom Lambda Authorizer ──────────────────────────
def authorizer_handler(event, context):
    """
    Invoked by API Gateway edge proxy to authorize microservice entry points.
    """
    print("\n[API Gateway Authorizer] Intercepting incoming execution API request...")
    token = event['authorizationToken'].replace('Bearer ', '')
    
    # Process cryptographic assertions 
    claims = mock_decode_and_validate_jwt(token)

    plan      = claims.get('subscription_plan', 'free')
    max_calls = int(claims.get('max_api_calls', 100))
    print(f"-> Authorizer evaluation: Tenant={claims.get('tenant_id')}, Tier={plan}, Limit={max_calls}")

    # Enforce access throttling boundaries based on claims token values
    if plan == 'free' and mock_is_rate_limited(claims['sub'], max_calls):
        print("-> Access Denied: Free tier execution boundary crossed.")
        raise Exception('Unauthorized')

    print(f"-> Access Granted: Emitting IAM Allow Policy execution frame.")
    return generate_policy(claims['sub'], 'Allow', event['methodArn'])

# ── Verification Harness Execution ────────────────────────────────────
if __name__ == "__main__":
    print("==================================================")
    print(" COGNITO CUSTOM CLAIMS & AUTHORIZATION PIPELINE")
    print("==================================================")

    # 1. Simulate Cognito Token Generation Request Event
    mock_cognito_event = {
        'userName': 'ml_engineer_test@example.com',
        'request': {'groupConfiguration': {}},
        'response': {}
    }
    
    token_output = pre_token_generation_trigger(mock_cognito_event, None)
    print(f"\nResulting Claims Mutation Block Struct:\n{json.dumps(token_output['response'], indent=2)}")

    # 2. Simulate API Gateway Authorizer Gateway Event
    mock_api_gateway_event = {
        'authorizationToken': 'Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjEifQ...',
        'methodArn': 'arn:aws:execute-api:ap-south-1:859977947607:api-id/prod/GET/models'
    }
    
    iam_policy_output = authorizer_handler(mock_api_gateway_event, None)
    print(f"\nEmitted API Gateway Policy Frame:\n{json.dumps(iam_policy_output, indent=2)}")

    print("\n==================================================")
    print(" END-TO-END JWT PIPELINE TESTING COMPLETE")
    print("==================================================")
