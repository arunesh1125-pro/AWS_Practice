import json
import boto3
from decimal import Decimal
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('SensorReadings')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj) if obj % 1 != 0 else int(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    try:
        # Extract query string parameters from API Gateway Proxy payload
        query_params = event.get('queryStringParameters') or {}
        
        action = query_params.get('action', 'QUERY_DEVICE')
        device_id = query_params.get('deviceId', 'device_lab_001')
        timestamp = query_params.get('timestamp', '')
        is_strong = query_params.get('strong', 'false').lower() == 'true'

        # ── Action 1: SAVE ───────────────────────────────────────────
        if action == 'SAVE':
            earp_val = float(query_params.get('earp', 0.35))
            speed_val = float(query_params.get('speed', 65.0))
            generated_ts = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            
            table.put_item(Item={
                'deviceId': device_id,
                'timestamp': generated_ts,
                'earpValue': Decimal(str(earp_val)),
                'speedKmh': Decimal(str(speed_val)),
                'drowsyAlert': earp_val < 0.25
            })
            return respond(201, {
                "status": "SUCCESS",
                "message": "Saved to DynamoDB",
                "deviceId": device_id,
                "timestamp": generated_ts
            })

        # ── Action 2: GET_SINGLE ──────────────────────────────────────
        elif action == 'GET_SINGLE':
            if not timestamp:
                return respond(400, {"status": "ERROR", "message": "Missing 'timestamp' parameter"})
            
            response = table.get_item(
                Key={'deviceId': device_id, 'timestamp': timestamp},
                ConsistentRead=is_strong,
                ReturnConsumedCapacity='TOTAL'
            )
            return respond(200, {
                "status": "SUCCESS",
                "read_type": "STRONGLY_CONSISTENT" if is_strong else "EVENTUALLY_CONSISTENT",
                "consumed_capacity": response.get('ConsumedCapacity', {}),
                "item": response.get('Item', "Not Found")
            })

        # ── Action 3: QUERY_DEVICE ────────────────────────────────────
        elif action == 'QUERY_DEVICE':
            response = table.query(
                KeyConditionExpression=Key('deviceId').eq(device_id),
                ScanIndexForward=False,
                Limit=10,
                ConsistentRead=is_strong,
                ReturnConsumedCapacity='TOTAL'
            )
            return respond(200, {
                "status": "SUCCESS",
                "read_type": "STRONGLY_CONSISTENT" if is_strong else "EVENTUALLY_CONSISTENT",
                "count": response.get('Count', 0),
                "consumed_capacity": response.get('ConsumedCapacity', {}),
                "readings": response.get('Items', [])
            })

        else:
            return respond(400, {"status": "ERROR", "message": f"Unknown lab action: {action}"})

    except Exception as e:
        return respond(500, {"status": "CRASHED", "error": str(e)})

def respond(status_code, body_content):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body_content, cls=DecimalEncoder)
    }
