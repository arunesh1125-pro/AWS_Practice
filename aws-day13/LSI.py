import json
import boto3
from decimal import Decimal
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
dynamodb_client = boto3.client('dynamodb', region_name='ap-south-1')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj) if obj % 1 != 0 else int(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    try:
        query_params = event.get('queryStringParameters') or {}
        action = query_params.get('action', 'QUERY_LSI')
        device_id = query_params.get('deviceId', 'device_lsi_001')
        is_strong = query_params.get('strong', 'false').lower() == 'true'

        # ── 1. CREATE LSI TABLE PROGRAMMATICALLY ───────────────────────
        if action == 'CREATE_LSI_TABLE':
            try:
                # Exam Focus: LSIs must be defined AT TABLE CREATION
                response = dynamodb_client.create_table(
                    TableName='SensorReadingsLSI',
                    AttributeDefinitions=[
                        {'AttributeName': 'deviceId',  'AttributeType': 'S'},
                        {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                        {'AttributeName': 'earpValue', 'AttributeType': 'N'} # Needed for LSI SK
                    ],
                    KeySchema=[
                        {'AttributeName': 'deviceId',  'KeyType': 'HASH'},  # Table PK
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}  # Table SK
                    ],
                    LocalSecondaryIndexes=[{
                        'IndexName': 'SensorReadings-ByEarpValue',
                        'KeySchema': [
                            {'AttributeName': 'deviceId',  'KeyType': 'HASH'},  # MUST match table PK
                            {'AttributeName': 'earpValue', 'KeyType': 'RANGE'}  # Alternative Sort Key
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    }],
                    BillingMode='PAY_PER_REQUEST'
                )
                return respond(201, {"status": "SUCCESS", "message": "SensorReadingsLSI table creation started."})
            except dynamodb_client.exceptions.ResourceInUseException:
                return respond(400, {"status": "ALREADY_EXISTS", "message": "Table already exists."})

        # ── 2. SAVE ITEM TO THE LSI TABLE ─────────────────────────────
        elif action == 'SAVE_LSI':
            earp_val = float(query_params.get('earp', '0.35'))
            speed_val = float(query_params.get('speed', '65.0'))
            generated_ts = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            
            lsi_table = dynamodb.Table('SensorReadingsLSI')
            lsi_table.put_item(Item={
                'deviceId': device_id,
                'timestamp': generated_ts,
                'earpValue': Decimal(str(earp_val)),
                'speedKmh': Decimal(str(speed_val)),
                'drowsyAlert': earp_val < 0.25
            })
            return respond(201, {"status": "SUCCESS", "message": "Saved to LSI table", "timestamp": generated_ts})

        # ── 3. QUERY VIA LOCAL SECONDARY INDEX ─────────────────────────
        elif action == 'QUERY_LSI':
            earp_threshold = float(query_params.get('earpMax', '0.50'))
            lsi_table = dynamodb.Table('SensorReadingsLSI')
            
            # Exam Focus: LSIs fully support Strongly Consistent Reads (ConsistentRead=True/False)
            response = lsi_table.query(
                IndexName='SensorReadings-ByEarpValue',
                KeyConditionExpression=
                    Key('deviceId').eq(device_id) & 
                    Key('earpValue').lt(Decimal(str(earp_threshold))),
                ConsistentRead=is_strong,
                ReturnConsumedCapacity='TOTAL'
            )
            return respond(200, {
                "status": "SUCCESS",
                "read_type": "STRONGLY_CONSISTENT" if is_strong else "EVENTUALLY_CONSISTENT",
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
