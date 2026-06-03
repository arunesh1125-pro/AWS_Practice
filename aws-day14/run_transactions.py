import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeDeserializer

dynamodb_client = boto3.client('dynamodb', region_name='ap-south-1')

def transfer_credits(from_user, to_user, amount):
    try:
        dynamodb_client.transact_write_items(
            TransactItems=[
                {
                    'Update': {
                        'TableName': 'UserCredits',
                        'Key': {'userId': {'S': from_user}},
                        'UpdateExpression': 'SET credits = credits - :amount',
                        'ConditionExpression': 'credits >= :amount',
                        'ExpressionAttributeValues': {':amount': {'N': str(amount)}}
                    }
                },
                {
                    'Update': {
                        'TableName': 'UserCredits',
                        'Key': {'userId': {'S': to_user}},
                        'UpdateExpression': 'SET credits = credits + :amount',
                        'ExpressionAttributeValues': {':amount': {'N': str(amount)}}
                    }
                },
                {
                    'Put': {
                        'TableName': 'TransactionAudit',
                        'Item': {
                            'txnId':    {'S': f"txn-{from_user}-{to_user}"},
                            'from':     {'S': from_user},
                            'to':       {'S': to_user},
                            'amount':   {'N': str(amount)},
                            'timestamp':{'S': '2026-06-04T03:00:00Z'}
                        }
                    }
                }
            ]
        )
        print(f"✅ SUCCESS: Transfer of {amount} credits from {from_user} to {to_user} succeeded.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'TransactionCanceledException':
            reasons = e.response['CancellationReasons']
            print(f"❌ CANCELLED: Transaction failed logic guards. Reason details: {reasons}")
        else:
            raise

def get_user_and_orders(user_id, order_id):
    print(f"\nPerforming atomic parallel reads for User: {user_id} and Order: {order_id}...")
    response = dynamodb_client.transact_get_items(
        TransactItems=[
            {'Get': {'TableName': 'Users', 'Key': {'userId': {'S': user_id}}}},
            {'Get': {'TableName': 'Orders', 'Key': {'customerId': {'S': user_id}, 'orderId': {'S': order_id}}}}
        ]
    )
    deserializer = TypeDeserializer()
    items = []
    for result in response['Responses']:
        if result.get('Item'):
            item = {k: deserializer.deserialize(v) for k, v in result['Item'].items()}
            items.append(item)
    return items

# --- Execution Workflow ---
if __name__ == "__main__":
    print("--- Test Case 1: Processing a standard valid transaction ---")
    transfer_credits(from_user="alice", to_user="bob", amount=30)

    print("\n--- Test Case 2: Forcing a balance failure guard (Alice only has 70 left) ---")
    transfer_credits(from_user="alice", to_user="bob", amount=500)

    print("\n--- Test Case 3: Executing transactional reads ---")
    fetched_data = get_user_and_orders(user_id="alice", order_id="ord-2026-99")
    print(f"Retrieved Atomic Records Data Set: {fetched_data}")
