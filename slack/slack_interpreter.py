import os
import json
import boto3
import logging
import urllib.request

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    trl = boto3.client('translate')

    B_TOKEN = os.getenv('TOKEN_B')
    O_TOKEN = os.getenv('TOKEN_O')
    api_msg_url = 'https://slack.com/api/chat.postMessage'
    ch = event.get('channel')
    header = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': f'Bearer {B_TOKEN}'
    }

    logging.info(json.dumps(event))

    if 'attachments' in event.get('messages')[0]:
        org_txt = event.get('messages')[0].get('attachments')[0].get('text')
        print(org_txt)
        
        res = trl.translate_text(
            Text=org_txt,
            SourceLanguageCode='en',
            TargetLanguageCode='ja'
        )
        
        interpreted = res['TranslatedText']
        print(interpreted)

        word = {
            'token': O_TOKEN,
            'channel': ch,
            'text': interpreted
        }
        
        req = urllib.request.Request(api_msg_url, data=json.dumps(word).encode('utf-8'), method='POST', headers=header)
        res = urllib.request.urlopen(req)

    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
