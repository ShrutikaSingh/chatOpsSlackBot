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

with open('command_config.json', 'r') as f:
    config = json.load(f)

commands = config.get('commands', {})
print(commands,"commands")

def hello(event, context):
    body = {
        "message": "Go Serverless v4.0! Your function executed successfully!"
    }
    return {"statusCode": 200, "body": json.dumps(body)}

def parse_slack_command(message):
    message_lower = message.lower()
    for cmd, cmd_data in commands.items():
        if any(keyword in message_lower for keyword in cmd.split()):
            return cmd, cmd_data
    return None, None


def invoke_lambda(function_name, event):
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

    body = parse_qs(event['body'])
    
    if 'command' not in body:
        return respond("Error: command key not found in event data")
    command_text = body['command'][0]

    print("Parsed command is:", command_text)
    command, cmd_data = parse_slack_command(command_text)

    if command:
        function_name = cmd_data['function']
        response = invoke_lambda(function_name, event)
        return respond(f"Successfullt triggered /{command}!")
    else:
        return respond(f"Unrecognized command: /{command_text}")

def second_lambda(event, context):
    print('invoked hello lambda')
    message = commands['hello']['message']
    #message = "Second Lambda says Hello"
    send_to_slack(message)
    return respond(message)


# create a third lamnda that says bye 
# some kind of spilt the message the
def third_lambda(event, context):
    print('invoked bye lambda')
    message = commands['bye']['message']
    #message = "Third Lambda says bye"
    send_to_slack(message)
    return respond(message)

def send_to_slack(message):
    slack_webhook_url = os.environ["SLACK_WEBHOOK_URL"]
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
        raise Exception(f"Request to Slack returned an error {response.status}, the response is:\n{response.data}, {message2}")

    return {
        'statusCode': 200,
        'body': json.dumps('Lambda finished  and notified Slack!, {message2}')
    }