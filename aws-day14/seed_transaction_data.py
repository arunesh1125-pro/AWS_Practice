import boto3

dynamodb = boto3.client("dynamodb", region_name="ap-south-1")

print("Seeding seed profile records...")
# 1. User Alice with 100 credits
dynamodb.put_item(
    TableName="UserCredits",
    Item={"userId": {"S": "alice"}, "credits": {"N": "100"}}
)
# 2. User Bob with 50 credits
dynamodb.put_item(
    TableName="UserCredits",
    Item={"userId": {"S": "bob"}, "credits": {"N": "50"}}
)
# 3. Target profile metadata for Get test
dynamodb.put_item(
    TableName="Users",
    Item={"userId": {"S": "alice"}, "name": {"S": "Alice Smith"}, "tier": {"S": "Premium"}}
)
# 4. Target order log data for Get test
dynamodb.put_item(
    TableName="Orders",
    Item={
        "customerId": {"S": "alice"},
        "orderId": {"S": "ord-2026-99"},
        "total": {"N": "299.50"},
        "status": {"S": "DELIVERED"}
    }
)
print("Data baseline successfully initialized!")
