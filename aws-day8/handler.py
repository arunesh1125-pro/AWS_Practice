import json
import boto3

# This is the handler — Lambda calls this function
# event = the input data (dict) from whatever triggered Lambda
# context = runtime info (function name, memory, time remaining)

def lambda_handler(event, context):
    # Print to CloudWatch Logs automatically
    print(f"Event Recived: {json.dumps(event)}")
    print(f"Function name: {context.function_name}")
    print(f"Time remaining: {context.get_remaining_time_in_millis()}ms")

    # Do your actual work
    name = event.get("name", "world")
    message = f"Hello, {name}!"

    # Return a response
    return{
        "statusCode": 200,
        "body": json.dumps({"message": message})
    }

# Handler string to enter in AWS Console: handler.lambda_handler

"""# Method 1: Run Locally via Terminal (Fastest)
if __name__ == "__main__":
    # Simulate a fake context object
    class MockContext:
        function_name = "local-test"
        def get_remaining_time_in_millis(self): return 300000

    # Simulate your input event
    test_event = {"name": "Developer"}

    # Run and print input event
    print(lambda_handler(test_event, MockContext()))"""