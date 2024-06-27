import json
import json
import boto3
import urllib3
import os
from urllib.parse import parse_qs
# from dotenv import load_dotenv
# load_dotenv()
# Initialize the AWS Lambda client
client = boto3.client('lambda')
http = urllib3.PoolManager()


def hello(event, context):
    body = {
        "message": "Go Serverless v4.0! Your function executed successfully!"
    }
    return {"statusCode": 200, "body": json.dumps(body)}

def parse_slack_command(message):
    print("at parse slack commmnad")
    commands = {
        'hello': ['hello', 'hi', 'good morning'],
        'bye': ['bye']
    }
    message_lower = message.lower()
    print("at message l", message_lower)
    for cmd, keywords in commands.items():
        print("inside first loop")
        for keyword in keywords:
            print("keyword", keyword)
            if keyword in message_lower:
                return cmd
    return None


def invoke_lambda(function_name, event):
    print("at invoke ,functiom name", function_name)
    return client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(event)
    )

def respond(message, extra_data=None):
    response = {
        'statusCode': 200,
        'body': json.dumps(message)
    }
    if extra_data:
        response['extra_data'] = extra_data
    return response

def first_lambda(event, context):
    print("here")
    print(event)

    body = parse_qs(event['body'])
    print("command array", body["command"])
    
    if 'command' not in body:
        print("command not found")
        return respond("Error: command key not found in event data")
    command_text = body['command'][0]

    print("main comand text", command_text)
    command = parse_slack_command(command_text)

    if command == 'hello':
        print("at hello 1")
        # Trigger second_lambda
        response = invoke_lambda('test2-dev-secondLambda', event) # update this with name in aws lambda console
    elif command == 'bye':
        print("at bye")
        # Trigger third_lambda
        response = invoke_lambda('test2-dev-thirdLambda', event)
    else:
        print("unrecognised")
        # Handle unrecognized command
        return respond(f"Unrecognized command: {command}")

    return respond(f"First Lambda executed and triggered {command} Lambda!", response)

def second_lambda(event, context):
    print('invoked hello lambda')
    message = "Second Lambda says Hello"
    send_to_slack(message)
    return respond(message)


# create a third lamnda that says bye 
# some kind of spilt the message the
def third_lambda(event, context):
    print('invoked bye lambda')
    message = "Third Lambda says bye"
    send_to_slack(message)
    return respond(message)

def send_to_slack(message):
    slack_webhook_url = os.environ["SLACK_WEBHOOK_URL"]
    print("mesaage is", message)
    message = {
        'text': message
    }
    encoded_data = json.dumps(message).encode('utf-8')
    
    response = http.request(
        'POST',
        slack_webhook_url,
        body=encoded_data,
        headers={'Content-Type': 'application/json'}
    )
   
    if response.status != 200:
        print("hello lamnda error")
        raise Exception(f"Request to Slack returned an error {response.status}, the response is:\n{response.data}, {message2}")

    return {
        'statusCode': 200,
        'body': json.dumps('Lambda finished  and notified Slack!, {message2}')
    }