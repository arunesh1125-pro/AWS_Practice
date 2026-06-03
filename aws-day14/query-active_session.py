import time
import boto3
from boto3.dynamodb.conditions import Attr, Key

dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
table = dynamodb.Table("UserSessions")

current_epoch = int(time.time())
print(f"Querying active sessions for user 'u001' (Current Epoch: {current_epoch})...")

response = table.query(
    IndexName="UserIndex",  # Uses our GSI
    KeyConditionExpression=Key("userId").eq("u001"),
    FilterExpression=Attr("expiresAt").gt(current_epoch),
)

items = response.get("Items", [])
print(f"\nFound {len(items)} unexpired session(s):")
for item in items:
    print(
        f" - SessionID: {item['sessionId']} | ExpiresAt: {item['expiresAt']} | Data: {item['sessionData']}"
    )
