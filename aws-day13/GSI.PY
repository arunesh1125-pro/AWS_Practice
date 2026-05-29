import json
import boto3
from decimal import Decimal
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
dynamodb_client = boto3.client('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('SensorReadings')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj) if obj % 1 != 0 else int(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    try:
        query_params = event.get('queryStringParameters') or {}
        action = query_params.get('action', 'QUERY_DEVICE')
        device_id = query_params.get('deviceId', 'device_lab_001')
        timestamp = query_params.get('timestamp', '')
        is_strong = query_params.get('strong', 'false').lower() == 'true'

        # ── 1. SAVE ITEM ───────────────────────────────────────────────
        if action == 'SAVE':
            earp_val = float(query_params.get('earp', 0.35))
            speed_val = float(query_params.get('speed', 65.0))
            generated_ts = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            
            # Note: GSI keys must be String, Number, or Binary. 
            # We convert boolean True/False to text strings 'TRUE'/'FALSE' for indexing compatibility.
            alert_string = 'TRUE' if earp_val < 0.25 else 'FALSE'
            
            table.put_item(Item={
                'deviceId': device_id,
                'timestamp': generated_ts,
                'earpValue': Decimal(str(earp_val)),
                'speedKmh': Decimal(str(speed_val)),
                'drowsyAlert': alert_string
            })
            return respond(201, {"status": "SUCCESS", "message": "Saved to DynamoDB", "timestamp": generated_ts})

        # ── 2. CREATE GLOBAL SECONDARY INDEX (GSI) PROGRAMMATICALLY ─────
        elif action == 'CREATE_INDEX':
            try:
                response = dynamodb_client.update_table(
                    TableName='SensorReadings',
                    AttributeDefinitions=[
                        {'AttributeName': 'drowsyAlert', 'AttributeType': 'S'},
                        {'AttributeName': 'timestamp',   'AttributeType': 'S'}
                    ],
                    GlobalSecondaryIndexUpdates=[{
                        'Create': {
                            'IndexName': 'AlertsByStatus',
                            'KeySchema': [
                                {'AttributeName': 'drowsyAlert', 'KeyType': 'HASH'}, # GSI Partition Key
                                {'AttributeName': 'timestamp',   'KeyType': 'RANGE'} # GSI Sort Key
                            ],
                            'Projection': {'ProjectionType': 'ALL'}, # Projects all table attributes into the GSI
                            'ProvisionedThroughput': {
                                'ReadCapacityUnits': 1,
                                'WriteCapacityUnits': 1
                            }
                        }
                    }]
                )
                return respond(200, {"status": "INDEX_CREATION_STARTED", "details": "AWS is building the index background."})
            except dynamodb_client.exceptions.ResourceInUseException:
                return respond(400, {"status": "ALREADY_EXISTS", "message": "Index is already created or currently processing."})

        # ── 3. QUERY VIA GLOBAL SECONDARY INDEX ────────────────────────
        elif action == 'QUERY_INDEX':
            alert_status = query_params.get('alertStatus', 'FALSE')
            
            # Exam Focus: GSIs do NOT support Strong Consistency. Force ConsistentRead=False.
            response = table.query(
                IndexName='AlertsByStatus',
                KeyConditionExpression=
                    Key('drowsyAlert').eq(alert_status) &
                    Key('timestamp').gt('2026-05-01T00:00:00Z'),
                ConsistentRead=False,
                ReturnConsumedCapacity='TOTAL'
            )
            return respond(200, {
                "status": "SUCCESS",
                "index_used": "AlertsByStatus",
                "count": response.get('Count', 0),
                "consumed_capacity": response.get('ConsumedCapacity', {}),
                "readings": response.get('Items', [])
            })

        else:
            return respond(400, {"status": "ERROR", "message": f"Unknown action: {action}"})

    except Exception as e:
        return respond(500, {"status": "CRASHED", "error": str(e)})

def respond(status_code, body_content):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body_content, cls=DecimalEncoder)
    }
