# Lambda handling WebSocket $connect route
import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
TABLE    = os.environ['CONNECTIONS_TABLE']

def lambda_handler(event, context):
    connection_id = event['requestContext']['connectionId']
    domain        = event['requestContext']['domainName']
    stage         = event['requestContext']['stage']

    # Store connection so we can push messages to this client later
    table = dynamodb.Table(TABLE)
    table.put_item(Item={
        'connectionId': connection_id,
        'endpoint': f"https://{domain}/{stage}",
        'connectedAt': event['requestContext']['connectedAt']
    })

    return {'statusCode': 200}


# Lambda pushing a message TO a connected client (server-initiated)
def push_to_client(connection_id, endpoint, message):
    apigw = boto3.client(
        'apigatewaymanagementapi',
        endpoint_url=endpoint    # must use the WebSocket management endpoint
    )

    try:
        apigw.post_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message).encode('utf-8')
        )
    except apigw.exceptions.GoneException:
        # Client disconnected — clean up from DynamoDB
        print(f"Connection {connection_id} is gone, removing...")