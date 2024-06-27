import json
import os
import boto3
import urllib3
from urllib.parse import parse_qs
client = boto3.client('lambda')
http = urllib3.PoolManager()

def hello(event, context):
    message = "Hello from your Slack command!"
    return respond(message)

def first_lambda(event, context):
    print("here")
    print(event)

    body = parse_qs(event['body'])
    print("Parsedbody:", body)
    print("command array", body["command"])
    
    # the commands comes in the body
    # like search hello
    # 'body': 'token=6VDtoVrYPIJJfGHQSbExJWEV&team_id=T079M1ZGV60&team_domain=chatops2workspace&channel_id=C07A7B8U7J4&channel_name=test&user_id=U07A7B50NAC&user_name=shrutika051220&command=%2Fhello&text=&api_app_id=A079M3B01HS&is_enterprise_install=false&response_url=https%3A%2F%2Fhooks.slack.com%2Fcommands%2FT079M1ZGV60%2F7347184392324%2F43GREJcOG6N2bseo93romKRB&trigger_id=7330146788727.7327067573204.d9bed3d16735772a4f30c342dab40f0d', 'isBase64Encoded': False}
    if 'command' not in body:
        print("command not found")
        return respond("Error: command key not found in event data")
    command_text = body['command'][0]
    print("main comand text", command_text)
    command = parse_slack_command(command_text)

    if command == 'hello':
        print("at hello 1")
        # Trigger second_lambda
        response = invoke_lambda('second_lambda', event)
    elif command == 'bye':
        print("at bye")
        # Trigger third_lambda
        response = invoke_lambda('third_lambda', event)
    else:
        print("unrecognised")
        # Handle unrecognized command
        return respond(f"Unrecognized command: {command}")

    return respond(f"First Lambda executed and triggered {command} Lambda!", response)

def second_lambda(event, context):
    print('hello invoking second lambda')
    message = "Hello Lambda executed successfully and trying to reply to slack!"
    # send_to_slack(message)
    
    slack_webhook_url = os.environ["SLACK_WEBHOOK_URL"]
  
    encoded_data = json.dumps(message).encode('utf-8')
    
    response = http.request(
        'POST',
        slack_webhook_url,
        body=encoded_data,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status != 200:
        error_message = f"Request to Slack returned an error {response.status}, the response is:\n{response.data.decode('utf-8')}"
        print(error_message)
        raise Exception(error_message)

    return {'message': 'Successfully sent message to Slack'}
    # return respond(message)

def third_lambda(event, context):
    print('byeinvoking second lambda')
    message = "Third Lambda says bye!"
    send_to_slack(message)
    return respond(message)

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
    return client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(event)
    )

def send_to_slack(message):
    slack_webhook_url = os.environ["SLACK_WEBHOOK_URL"]
  
    encoded_data = json.dumps(message).encode('utf-8')
    
    response = http.request(
        'POST',
        slack_webhook_url,
        body=encoded_data,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status != 200:
        error_message = f"Request to Slack returned an error {response.status}, the response is:\n{response.data.decode('utf-8')}"
        print(error_message)
        raise Exception(error_message)

    return {'message': 'Successfully sent message to Slack'}

def respond(message, extra_data=None):
    response = {
        'statusCode': 200,
        'body': json.dumps(message)
    }
    if extra_data:
        response['extra_data'] = extra_data
    return response
