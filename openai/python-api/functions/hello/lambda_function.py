import os
import sys
import hashlib
import hmac
import time
import json
import logging
from typing import List, Dict, Sequence, Tuple, Type, TypeVar, Union, Any

import requests
import boto3
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.memory.chat_message_histories import DynamoDBChatMessageHistory
# from langchain import OpenAI, LLMChain, PromptTemplate
# from langchain.memory import ConversationBufferWindowMemory

SLACK_SIGNING_SECRET = os.environ['SLACK_SIGNING_SECRET']

h = logging.StreamHandler(sys.stdout)
logger = logging.getLogger(__name__)
for handler in logger.handlers:
    logger.removeHandler(handler)

format = logging.Formatter('%(asctime)s [%(levelname)s](%(name)s: %(lineno)d)  :%(message)s')
h.setFormatter(format)
logger.addHandler(h)
logger.setLevel(logging.INFO)


class chatHistory:
    # DynamoDBテーブルにOpenAIの応答を保存し、次回の応答に利用する
    # method: save_history, get_history
    table = os.getenv('TABLE_NAME')

    def __init__(self, userId, timestamp, message: list):
        self.userId = userId
        self.timestamp = timestamp # unit: second
        self.message = '¥n'.join(message)

        self.client = self.init_client()
        self.key_time = str(self.timestamp // 10000 * 10000)
        self.ttl = str(int(time.time()) + 60 * 60 * 24) # 1 day

    def init_client(self):
        dynamodb = boto3.client('dynamodb')
        return dynamodb            

    def save_history(self):
        item = {
            'sessionId': {
                'S': self.userId
            },
            'createdAt': {
                'N': str(self.timestamp)
            },
            'keyTime': {
                'N': self.key_time
            },
            'message': {
                'S': self.message
            },
            'ttl': {
                'N': self.ttl
            },
        }
        logger.info(item)
        self.client.put_item(
            TableName=self.table,
            Item=item,
        )

    def get_history(self):
        response = self.client.query(
            TableName=self.table,
            KeyConditionExpression='sessionId = :session',
            # KeyConditionExpression='sessionId = :session and keyTime = :keyTime',
            ExpressionAttributeValues={
                ':session': {
                    'S': self.userId
                },
                # ':keyTime': {
                #     'N': self.key_time
                # }
            },
            ProjectionExpression='message',
        )['Items']
        logger.info(response)
        if response:
            history = ''
            for i in response:
                if 'message' in i:
                    history += i['message']['S'] + '¥n'
            return history
        else:
            return ''

def respond_slack_challenge(event_body):
    # slack_event = json.loads(event['body'])

    return {'statusCode': 200, 'body': json.dumps({'challenge': event_body['challenge']})}

def verify_slack_signature(event):
    slack_signature = event['headers']['X-Slack-Signature']
    slack_request_timestamp = event['headers']['X-Slack-Request-Timestamp']

    # 署名を構成する
    sig_base = f"v0:{slack_request_timestamp}:{event['body']}".encode('utf-8')
    my_signature = 'v0=' + hmac.new(
        os.environ['SLACK_SIGNING_SECRET'].encode('utf-8'),
        sig_base,
        hashlib.sha256
    ).hexdigest()

    # 署名が一致するか検証
    return hmac.compare_digest(my_signature, slack_signature)    


def post_slack_message(slackbot_token, channel_id, msg):
    url = 'https://slack.com/api/chat.postMessage'
    headers = {
        'Authorization': f"Bearer {slackbot_token}",
        'Content-Type': 'application/json'
    }
    payload = {
        'channel': channel_id,
        'text': msg
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if respose.status_code != 200:
        logger.error(response.text)
        raise Exception('Failed to Post Slack API')
    else:
        return response.json()


def handler(event, context):
    logger.info(json.dumps(event))

    chatApiKey = os.environ['OPENAI_API_KEY']
    chat = ChatOpenAI(model_name='gpt-3.5-turbo-16k', temperature=0.7, openai_api_key=chatApiKey, max_tokens=5000, verbose=True)

    user_id = event['requestContext']['identity']['sourceIp']
    timestamp = event['requestContext']['requestTimeEpoch'] // 1000
    
    # chat_history = DynamoDBChatMessageHistory(
    #     table_name=os.environ['TABLE_NAME'],
    #     session_id=f"{user_id}-{str(timestamp)}",
    # )

    system_preset = 'You are a {role}, all the answer must be with confidence value between 0 and 10.'
    human_input = '{history}' + '¥n' + 'Tell me What you can provide, and What a type of input you can better respond?'

    if 'body' in event:
        body = json.loads(event['body'])

        if 'challenge' in body:
            respond_slack_challenge(body)

        elif verify_slack_signature(event):        
            try:
                # input_prompt = body['user_input']
                input_prompt = body['event']['text']
                logger.info('input: ' + human_input)
            except KeyError:
                pass
                logger.info('Input Pamameter does not exist in the request body.')
                input_prompt = 'There is no prompt properly.'
            human_input = '{history}' + '¥n' + input_prompt
    
    chat_history = chatHistory(user_id, timestamp, [human_input])
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_preset)
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_input)

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )
    old_messages = chat_history.get_history()
    reply = chat(
        chat_prompt.format_prompt(
            role='professional for science, technology, and humanities',
            history=old_messages,
        ).to_messages()
    )

    # ex.) reply = ('content', "I'm sorry, but I cannot understand the text you provided. Could you please rephrase or provide more context?"), ('additional_kwargs', {}), ('example', False)
    for i in reply:            
        if i[0] == 'content':
            reply_content = i[1]
            logger.info('output: ' + reply_content)
            break

    if reply_content:
        chat_history = chatHistory(user_id, timestamp, ['Human:' + human_input, 'AI:' + reply_content])
        chat_history.save_history()

        res = post_slack_message(
            os.getenv('SLACK_BOT_TOKEN'),
            body['event']['channel'],
            reply_content
        )
        logger.info(res)

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json; charset=utf-8'
            },
            'body': json.dumps(reply_content, ensure_ascii=False)
        }

