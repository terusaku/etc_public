import os
import json
import boto3
import logging
import urllib.request

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
#def lambda_handler(event: dict, context):
    
    client = boto3.client('lambda')

    KEY_WORD = 'hello'
    re_WORD = os.getenv('REPLY')
    REACTION = os.getenv('REACTION')
    B_TOKEN = os.getenv('TOKEN_B')
    O_TOKEN = os.getenv('TOKEN_O')
    api_msg_url = 'https://slack.com/api/chat.postMessage'
    api_hist_url = 'https://slack.com/api/channels.history'
    api_info_url = 'https://slack.com/api/files.info'
    api_up_url = 'https://slack.com/api/files.upload'
    BACKEND = os.getenv('BACKEND')

    logging.info(json.dumps(event))

    if "challenge" in event:
        key = event.get('challenge')
        return {
            'isBase64Encoded': 'true',
            'statusCode': 200,
            'headers': {},
            'body': key
        }

    elif "body" in event:
        d = event.get('body')
        key = d.get('challenge')
        
        if "challenge" in d:
            return {
                'isBase64Encoded': 'true',
                'statusCode': 200,
                'headers': {},
                'body': key
            }
    else:
        d = event

    if "url_private_download" in d:
        ch = d.get('event').get('channel')
        load_url = d.get('event').get('files')[0].get('url_private_download')
        print(load_url)

        res = client.invoke(
            FunctionName='hello-py',
            InvocationType='Event',
            LogType='Tail',
            Payload= d
        )

        return {'statusCode': 200, 'body': 'ok'}

    
    if d.get('event').get('text') == KEY_WORD:
        header = {
            'Content-Type': 'application/json; charset=UTF-8',
            'Authorization': 'Bearer {0}'.format(B_TOKEN)
        }

        ch = d.get('event').get('channel')
        word = {
            'token': O_TOKEN,
            'channel': ch,
            'text': re_WORD
        }
        
        req = urllib.request.Request(api_msg_url, data=json.dumps(word).encode('utf-8'), method='POST', headers=header)
        res = urllib.request.urlopen(req)
        return {'statusCode': 200, 'body': 'ok'}
    
    if d.get('event').get('type') == 'reaction_added':
        header = {
            'Content-Type': 'application/json; charset=UTF-8',
            'Authorization': 'Bearer {0}'.format(B_TOKEN)
        }
        ch = d.get('event').get('item').get('channel')
        msg_time = d.get('event').get('item').get('ts')

        if d.get('event').get('reaction') == 'sos':

            msg = {
                'token': O_TOKEN,
                'channel': ch,
                'latest': msg_time,
                'inclusive': 'true',
                'count': 1 
            }
#            req_msg = urllib.request.Request(api_hist_url, data=json.dumps(msg).encode('utf-8'), method='GET', headers=header)
            req_msg = urllib.request.Request(api_hist_url)
            data_msg = urllib.parse.urlencode(msg).encode('utf-8')
            req_msg.data = data_msg
            res_msg = urllib.request.urlopen(req_msg)

            msg_read = json.loads(res_msg.read())
            msg_read.update({'channel': ch})
            logger.info(json.dumps(msg_read))

        react = {
            'token': O_TOKEN,
            'channel': ch,
            'text': f'Invoking Lambda function {BACKEND} {re_WORD}'
        }
        req = urllib.request.Request(api_msg_url, data=json.dumps(react).encode('utf-8'), method='POST', headers=header)
        res = urllib.request.urlopen(req)
        
        res_translate = client.invoke(
            FunctionName=BACKEND,
            InvocationType='Event',
            LogType='Tail',
            Payload= json.dumps(msg_read)
        )


        return {'statusCode': 200, 'body': 'ok'}
    

    return {
        'statusCode': 200,
        'body': json.dumps('quit')
    }
    