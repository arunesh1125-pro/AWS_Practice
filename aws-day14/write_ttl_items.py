import time
from datetime import datetime, timezone
import boto3

dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
table = dynamodb.Table("UserSessions")


def create_session(user_id, session_data, ttl_hours=24, force_expired=False):
    current_time = int(time.time())

    # If force_expired is True, make it expire 1 hour ago
    if force_expired:
        expiry_time = current_time - 3600
    else:
        expiry_time = current_time + (ttl_hours * 3600)

    session_id = f"sess-{user_id}-{current_time}"

    table.put_item(
        Item={
            "sessionId": session_id,
            "userId": user_id,
            "sessionData": session_data,
            "createdAt": datetime.now(timezone.utc).isoformat() + "Z",
            "expiresAt": expiry_time,  # Unix Epoch Seconds
        }
    )
    print(
        f"Created session {session_id} (Expires Epoch: {expiry_time}, Expired: {force_expired})"
    )


print("Injecting test payloads...")
# 1. Valid Active Session
create_session(user_id="u001", session_data={"theme": "dark"}, ttl_hours=24)

# 2. Expired Session (Still readable until background sweep deletes it)
create_session(
    user_id="u001",
    session_data={"theme": "light"},
    ttl_hours=0,
    force_expired=True,
)
