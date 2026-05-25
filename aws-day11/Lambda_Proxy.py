# Lambda receives the FULL request object from API Gateway
def lambda_handler(event, context):
    # event contains everything API Gateway received
    method      = event['httpMethod']           # GET, POST, etc.
    path        = event['path']                 # /predict
    headers     = event['headers']             # all HTTP headers
    query_params = event['queryStringParameters'] or {}
    body        = event['body']                 # request body (string)
    path_params = event['pathParameters'] or {} # /users/{id}

    # Parse body if JSON
    import json
    if body:
        payload = json.loads(body)
    else:
        payload = {}

    user_id = path_params.get('id')
    model = query_params.get('model', 'default')

    # Process...
    result = run_inference(payload, model)

    # Lambda MUST return this exact structure for proxy integration
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
            },
        "body": json.dumps({
            "user_id": user_id,
            "prediction": result,
            "model": model
            })
    }
    # statusCode and body are REQUIRED
    # Missing statusCode → API Gateway returns 502 Bad Gateway