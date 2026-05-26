import requests
import json

# YOUR REAL API ID AND PATH FROM PREVIOUS STEPS
API_URL = 'https://ul6o4f6y6f.execute-api.ap-south-1.amazonaws.com/prod/users/{12345}'

print("Sending API Gateway request with cache invalidation header...")

# Query string parameters
query_params = {
    'model': 'v4'
}

# Custom header to trigger cache invalidation
custom_headers = {
    'Cache-Control': 'max-age=0',
    'Content-Type': 'application/json'
}

# Body payload required for POST method integration
body_payload = {
    'sample_data': 'Testing cache bypass'
}

try:
    # Changed to .post() to match your API Gateway resource method
    response = requests.post(
        API_URL,
        params=query_params,
        headers=custom_headers,
        data=json.dumps(body_payload)  # Convert dict to JSON string
    )

    print(f"✅ Status Code Received: {response.status_code}")
    print("Response JSON Payload:")
    print(json.dumps(response.json(), indent=4))

except Exception as e:
    print(f"❌ Connection Error: {str(e)}")