import os
import json
import urllib.parse
import logging

import boto3
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
# from langchain import OpenAI, LLMChain, PromptTemplate
# from langchain.memory import ConversationBufferWindowMemory

format = logging.Formatter('%(asctime)s (%(name)s: %(lineno)d) [%(levelname)s] :%(message)s')
handler = logging.StreamHandler().setFormatter(format)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def handler(event, context):
    logger.info(json.dumps(event))

    chatApiKey = os.environ['OPENAI_API_KEY']
    chat = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0.7, openai_api_key=chatApiKey, max_tokens=4000, verbose=True)

    system_preset = 'You are a {role}, all the answer must be with confidence value between 0 and 10.'
    human_input = 'Tell me What you can provide, and What a type of input you can better respond?'
    if 'body' in event:
        body = json.loads(event['body'])
        try:
            human_input = body['user_input']
            logger.info('input: ' + human_input)
        except KeyError:
            pass
            logger.info('`user_input` does not exist in the request body.')

    system_message_prompt = SystemMessagePromptTemplate.from_template(system_preset)
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_input)

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )
    reply = chat(
        chat_prompt.format_prompt(
            role='professional for science, technology, and humanities',
        ).to_messages()
    )

    # ex.) reply = ('content', "I'm sorry, but I cannot understand the text you provided. Could you please rephrase or provide more context?"), ('additional_kwargs', {}), ('example', False)
    for i in reply:            
        if i[0] == 'content':
            reply_content = i[1]
            logger.info('output: ' + reply_content)
            break
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json; charset=utf-8'
        },
        'body': json.dumps(reply_content, ensure_ascii=False)
    }

    # template = '''
    # {history}
    # System: {system_presets}
    # Human: {user_input}
    # Assistant: 
    # '''

    # chat_prompt = PromptTemplate(
    #     input_variables=['history', 'system_presets', 'user_input'],
    #     template=template,
    # )

    # openai_client = OpenAI(
    #     temperature=0.7,
    #     model_name='gpt-4',
    #     max_tokens=500,        
    # )
    # chatgp_chain = LLMChain(
    #     llm=openai_client,
    #     prompt=chat_prompt,
    #     verbose=True,
    #     memory=ConversationBufferWindowMemory(k=10),
    # )
    
    # history = ''
    # reply = chatgp_chain.predict(
    #     history=history,
    #     system_presets=preset,
    #     user_input='Hello, I am a human.'
    # )

