import json
import boto3
import os
import urllib3
from urllib.parse import parse_qs

http = urllib3.PoolManager()

with open('command_config.json', 'r') as f:
    config = json.load(f)

def respond(message, extra_data=None):
    response = {
        'statusCode': 200,
        'body': json.dumps(message)
    }
    if extra_data:
        response['extra_data'] = extra_data
    return response

def third_lambda(event, context):
    if 'body' not in event:
        return respond("Error: Body not found in event data")

    try:
        if event['headers'].get('Content-Type') == 'application/json':
            body = json.loads(event['body'])
        else:
            body = parse_qs(event['body'])

        if isinstance(body, dict) and body.get('type') == 'url_verification':
            return {
                'statusCode': 200,
                'body': body['challenge']
            }

        if 'payload' in body:
            payload = json.loads(body['payload'][0])
            if payload['type'] == 'interactive_message':
                # Handle dropdown selections
                selected_service = payload['actions'][0]['selected_options'][0]['value']
                trigger_id = payload['trigger_id']
                return open_action_dropdown(trigger_id, selected_service)
            elif payload['type'] == 'dialog_submission':
                submission = payload['submission']
                service = payload['callback_id'].split('_')[0]
                action = payload['callback_id'].split('_')[1]
                params = {key: value for key, value in submission.items()}
                return perform_action(service, action, params)
            else:
                return respond("Error: Unsupported payload type")

        if 'command' in body:
            command_text = body['command'][0]

            if command_text == '/aws':
                if 'trigger_id' not in body:
                    return respond("Error: trigger_id not found in event data")

                trigger_id = body['trigger_id'][0]
                return open_service_dropdown(trigger_id)

            return respond(f"Unrecognized command: {command_text}")

        return respond("Error: Invalid request format")

    except Exception as e:
        return respond(f"Error: {str(e)}")

def open_service_dropdown(trigger_id):
    services = list(config['services'].keys())
    dialog = {
        "trigger_id": trigger_id,
        "dialog": {
            "callback_id": "select_service",
            "title": "Select AWS Service",
            "elements": [
                {
                    "type": "select",
                    "label": "Service",
                    "name": "service",
                    "options": [{"label": service, "value": service} for service in services]
                }
            ]
        }
    }

    return send_dialog_to_slack(dialog)

def open_action_dropdown(trigger_id, service):
    actions = list(config['services'][service]['actions'].keys())
    dialog = {
        "trigger_id": trigger_id,
        "dialog": {
            "callback_id": f"{service}_select_action",
            "title": f"Select Action for {service}",
            "elements": [
                {
                    "type": "select",
                    "label": "Action",
                    "name": "action",
                    "options": [{"label": action, "value": action} for action in actions]
                }
            ]
        }
    }

    return send_dialog_to_slack(dialog)

def open_action_parameters_dialog(trigger_id, service, action):
    parameters = config['services'][service]['actions'][action]['parameters']
    dialog_elements = [
        {"type": "text", "label": key, "name": key, "value": value} for key, value in parameters.items()
    ]
    dialog = {
        "trigger_id": trigger_id,
        "dialog": {
            "callback_id": f"{service}_{action}",
            "title": f"Parameters for {service} {action}",
            "elements": dialog_elements
        }
    }

    return send_dialog_to_slack(dialog)

def send_dialog_to_slack(dialog):
    if 'SLACK_BOT_TOKEN' not in os.environ:
        return respond("Error: SLACK_BOT_TOKEN environment variable not set")

    slack_response = http.request(
        'POST',
        'https://slack.com/api/dialog.open',
        body=json.dumps(dialog).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {os.environ['SLACK_BOT_TOKEN']}"
        }
    )

    print("Slack Response Status:", slack_response.status)
    print("Slack Response Data:", slack_response.data.decode('utf-8'))

    if slack_response.status != 200 or json.loads(slack_response.data.decode('utf-8')).get('ok') is not True:
        return respond(f"Error: Unable to open dialog - {slack_response.data}")

    return respond("Dialog sent to Slack!")

def perform_action(service, action, params):
    if service == "ec2":
        return handle_ec2_action(action, params)
    elif service == "s3":
        return handle_s3_action(action, params)
    elif service == "iam":
        return handle_iam_action(action, params)
    else:
        return respond(f"Unsupported service: {service}")

def handle_ec2_action(action, params):
    ec2 = boto3.client('ec2')
    if action == "create":
        response = ec2.run_instances(
            ImageId=params['ami'],
            InstanceType=params['instance_type'],
            KeyName=params['key_name'],
            MaxCount=1,
            MinCount=1,
            Placement={'AvailabilityZone': params['region']}
        )
    elif action == "start":
        response = ec2.start_instances(InstanceIds=[params['instance_id']])
    elif action == "stop":
        response = ec2.stop_instances(InstanceIds=[params['instance_id']])
    elif action == "terminate":
        response = ec2.terminate_instances(InstanceIds=[params['instance_id']])
    else:
        return respond(f"Unsupported EC2 action: {action}")

    return respond(response)

def handle_s3_action(action, params):
    s3 = boto3.client('s3')
    if action == "create":
        response = s3.create_bucket(
            Bucket=params['bucket_name'],
            CreateBucketConfiguration={'LocationConstraint': params['region']}
        )
    else:
        return respond(f"Unsupported S3 action: {action}")

    return respond(response)

def handle_iam_action(action, params):
    iam = boto3.client('iam')
    if action == "create_user":
        response = iam.create_user(UserName=params['user_name'])
    else:
        return respond(f"Unsupported IAM action: {action}")

    return respond(response)
