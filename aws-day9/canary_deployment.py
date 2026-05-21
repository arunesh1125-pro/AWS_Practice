import boto3
import time

lambda_client = boto3.client('lambda', region_name='ap-south-1')
FUNCTION_NAME = 'ml-inference-function'

# PHASE 1: CANARY DEPLOYMENT
print("Phase 1: Starting Canary Deployment...")
print("Routing 90% of traffic to Version 5 and 10% to Version 6...")

lambda_client.update_alias(
    FunctionName=FUNCTION_NAME,
    Name = 'prod',
    FunctionVersion='5',
    RoutingConfig={
        'AdditionalVersionWeights': {
            '6': 0.10    # 10% to Version 6
        }
    }
)
print("Canary routing successfully applied!")
time.sleep(2)  # Pause to simulate monitoring period

# PHASE 2: FULL PROMOTION
print("\nPhase 2: Promoting Version 6 to 100% traffic...")

lambda_client.update_alias(
    FunctionName=FUNCTION_NAME,
    Name='prod',
    FunctionVersion='6',
    RoutingConfig={
        'AdditionalVersionWeights': {}   # empty = 100% to version 6
    }
)
print("Version 6 is now handling 100% of production traffic!")
time.sleep(2)  # Pause to simulate a post-deployment issue popping up

# PHASE 3: INSTANT ROLLBACK
print("\nPhase 3: Alert triggered! Executing instant rollback to Version 5...")

lambda_client.update_alias(
    FunctionName=FUNCTION_NAME,
    Name='prod',
    FunctionVersion='5',
    RoutingConfig={
        'AdditionalVersionWeights': {}   # empty = 100% to version 5
    }
)
print("Rollback complete. Production traffic safely secured back on Version 5.")