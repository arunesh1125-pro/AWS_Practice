import json
import boto3
import threading
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('SensorReadingsLSI')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj) if obj % 1 != 0 else int(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    try:
        query_params = event.get('queryStringParameters') or {}
        action = query_params.get('action', 'LAB_QUERY')
        device_id = query_params.get('deviceId', 'driver_lsi_99')

        # ── 1. EFFICIENT QUERY OPERATION ───────────────────────────────
        if action == 'LAB_QUERY':
            # Exam Focus: ProjectionExpression allows dropping attributes to save transfer payload bandwidth
            # 'timestamp' is an AWS reserved word, requiring ExpressionAttributeNames (#ts) [1]
            response = table.query(
                KeyConditionExpression=Key('deviceId').eq(device_id),
                FilterExpression=Attr('drowsyAlert').eq(False), # Evaluated AFTER table read [1]
                ProjectionExpression='deviceId, #ts, earpValue, speedKmh',
                ExpressionAttributeNames={'#ts': 'timestamp'},
                ReturnConsumedCapacity='TOTAL'
            )
            return respond(200, {
                "operation": "QUERY",
                "count_returned": response.get('Count', 0),        # Final filtered array size [1]
                "scanned_count_billed": response.get('ScannedCount', 0), # Items read from disk [1]
                "consumed_capacity": response.get('ConsumedCapacity', {}),
                "items": response.get('Items', [])
            })

        # ── 2. SEQUENTIAL TABLE SCAN OPERATION ─────────────────────────
        elif action == 'LAB_SCAN':
            # Exam Focus: Scans look at every item in the entire table blindly
            response = table.scan(
                FilterExpression=Attr('drowsyAlert').eq(False),
                ReturnConsumedCapacity='TOTAL'
            )
            return respond(200, {
                "operation": "SEQUENTIAL_SCAN",
                "count_returned": response.get('Count', 0),
                "scanned_count_billed": response.get('ScannedCount', 0),
                "consumed_capacity": response.get('ConsumedCapacity', {}),
                "items": response.get('Items', [])
            })

        # ── 3. MULTI-THREADED PARALLEL SCAN OPERATION ──────────────────
        elif action == 'LAB_PARALLEL_SCAN':
            # Exam Focus: Parallel scanning accelerates massive table reads using segments [1]
            total_segments = 4
            shared_results = []
            threads = []
            capacity_tracked = 0.0

            def scan_segment(segment_id):
                nonlocal capacity_tracked
                res = table.scan(
                    TotalSegments=total_segments,
                    Segment=segment_id,
                    ReturnConsumedCapacity='TOTAL'
                )
                shared_results.extend(res.get('Items', []))
                if 'ConsumedCapacity' in res:
                    capacity_tracked += float(res['ConsumedCapacity'].get('CapacityUnits', 0))

            # Spin up 4 concurrent isolated worker threads [1]
            for i in range(total_segments):
                t = threading.Thread(target=scan_segment, args=(i,))
                threads.append(t)
                t.start()

            # Wait for all thread operations to join back safely [1]
            for t in threads:
                t.join()

            return respond(200, {
                "operation": "PARALLEL_SCAN",
                "total_segments_processed": total_segments,
                "total_items_found": len(shared_results),
                "aggregated_capacity_cost": capacity_tracked,
                "items": shared_results
            })

        else:
            return respond(400, {"status": "ERROR", "message": f"Unknown action mapping: {action}"})

    except Exception as e:
        return respond(500, {"status": "CRASHED", "error": str(e)})

def respond(status_code, body_content):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body_content, cls=DecimalEncoder)
    }
