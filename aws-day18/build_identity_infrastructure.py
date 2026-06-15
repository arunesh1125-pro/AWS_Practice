import boto3

USER_POOL_ID   = 'ap-south-1_nZlIt8tqo'
CLIENT_ID      = '5afv1vumh632q9bgeqjto3lebn'
ROLE_ARN       = 'arn:aws:iam::859977947607:role/Cognito_MLEngineer_Role'
PROVIDER_STR   = f'cognito-idp.ap-south-1.amazonaws.com/{USER_POOL_ID}'

# Use your existing generated Identity Pool ID directly
POOL_ID_FINAL  = 'ap-south-1:be44c608-8c7e-4443-b577-fda5c50849d6'

identity_client = boto3.client('cognito-identity', region_name='ap-south-1')

def bind_infrastructure_roles():
    print(f"Targeting Identity Pool ID: {POOL_ID_FINAL}")
    print("\nStep 2: Attaching security role mapping matrices to Identity Pool rules...")
    
    identity_client.set_identity_pool_roles(
        IdentityPoolId=POOL_ID_FINAL,
        Roles={'authenticated': ROLE_ARN},
        RoleMappings={
            f"{PROVIDER_STR}:{CLIENT_ID}": {
                'Type': 'Token',  # FIX: Correct AWS Boto3 Enum value
                'AmbiguousRoleResolution': 'AuthenticatedRole'
            }
        }
    )
    print("SUCCESS: Attached token resolution group mappings completely.")

if __name__ == "__main__":
    print("==================================================")
    print(" RE-BINDING COGNITO FEDERATED IDENTITY POOL ROLES")
    print("==================================================")
    bind_infrastructure_roles()
