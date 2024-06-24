import json
import json
import boto3
import urllib3
import os
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


def first_lambda(event, context):
    slack_webhook_url = os.environ["SLACK_WEBHOOK_URL"]
  
    response = client.invoke(
        FunctionName='test2-dev-secondLambda',
        InvocationType='RequestResponse',
        Payload=json.dumps(event)
    )
    
    # where the first lambda triggered by the user message say hello in slack
    # first lambda command undertsnad the command and trigger 
    # if heelo second lambda if bye third lamda

    # the idea is to parse the message ex: echo my lambda, echo as signal and whatever comes after as paramter
    # find a parser that allows us to send options to it

    message = f"First Lambda executed and triggered the second Lambda! {slack_webhook_url}"

    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }

def second_lambda(event, context):
    slack_webhook_url = os.environ["SLACK_WEBHOOK_URL"]
  
    message = {
        'text': 'Second Lambda executed successfully!'
    }

    message2 = f"Second Lambda executed and triggered the second Lambda! {slack_webhook_url}"

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
        'body': json.dumps('Second Lambda executed and notified Slack!, {message2}')
    }


# create a third lamnda that says bye 
# some kind of spilt the message the
