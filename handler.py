import json
import boto3
import urllib3
import os
from urllib.parse import parse_qs

# Initialize the AWS Lambda client
client = boto3.client('lambda')
http = urllib3.PoolManager()

with open('command_config.json', 'r') as f:
    config = json.load(f)

commands = config.get('commands', {})
print(commands, "commands")

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
        return respond(f"Successfully triggered /{command}!")
    else:
        return respond(f"Unrecognized command: /{command_text}")

def second_lambda(event, context):
    print('invoked hello lambda')
    message = commands['hello']['message']
    send_to_slack(message)
    return respond(message)

def third_lambda(event, context):
    print('invoked bye lambda')

    if 'body' not in event:
        return respond("Error: Body not found in event data")
    
    body = parse_qs(event['body'])

    if 'payload' in body:
        payload = json.loads(body['payload'][0])
        if payload['type'] == 'dialog_submission':
            submission = payload['submission']
            user_to = submission.get('to', 'Default User')
            region = submission.get('region', 'Default Region')
            additional_message = submission.get('additional_message', 'No additional message')

            print('printing', 'user_to', user_to, 'region', region, 'additional_message', additional_message)

            message = f"Goodbye from Third Lambda! to {user_to} region: {region} additional message: {additional_message}"
            send_to_slack(message)
            return respond(message)
        else:
            return respond("Error: Unsupported payload type")

    if 'command' not in body:
        return respond("Error: command key not found in event data")
    
    command_text = body['command'][0]

    if command_text == '/bye':
        if 'trigger_id' not in body:
            return respond("Error: trigger_id not found in event data")
        
        trigger_id = body['trigger_id'][0]
        dialog = {
            "trigger_id": trigger_id,
            "dialog": {
                "callback_id": "bye_dialog",
                "title": "Goodbye Details",
                "submit_label": "Submit",
                "elements": [
                    {
                        "type": "text",
                        "label": "To",
                        "name": "to",
                        "placeholder": "Enter recipient"
                    },
                    {
                        "type": "text",
                        "label": "Region",
                        "name": "region",
                        "placeholder": "Enter region"
                    },
                    {
                        "type": "textarea",
                        "label": "Additional Message",
                        "name": "additional_message",
                        "optional": True
                    }
                ]
            }
        }

        if 'SLACK_BOT_TOKEN' not in os.environ:
            return respond("Error: SLACK_BOT_TOKEN environment variable not set")

        print("Dialog Payload:", json.dumps(dialog))

        slack_response = http.request(
            'POST',
            'https://slack.com/api/dialog.open',
            body=json.dumps(dialog).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {os.environ['SLACK_BOT_TOKEN']}"
            }
        )

        print("Slack Response:", slack_response.status, slack_response.data)

        if slack_response.status != 200 or json.loads(slack_response.data.decode('utf-8')).get('ok') is not True:
            return respond(f"Error: Unable to open dialog - {slack_response.data}")

        return respond("Dialog sent to Slack!")

    return respond(f"Unrecognized command: {command_text}")

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
        raise Exception(f"Request to Slack returned an error {response.status}, the response is:\n{response.data}")

    return {
        'statusCode': 200,
        'body': json.dumps('Lambda finished and notified Slack!')
    }
