import os
import json

import requests
from langchain import OpenAI, LLMChain, PromptTemplate
from langchain.memory import ConversationBufferWindowMemory


def handler(event, context):

    print(json.dumps(event))

    baseURL = 'https://api.openai.com/v1'
    chatApiKey = os.environ['OPENAI_API_KEY']
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {chatApiKey}",
    }

    system_preset = """
    You are a professional for science, technology, and humanities.
    """
    template = """
    {history}
    System: {system_presets}
    Human: {user_input}
    Assistant: 
    """
    
    chat_prompt = PromptTemplate(
        input_variables=['history', 'user_input'],
        template=template,    
    )

    openai_client = OpenAI(
        temperature=0.7,
        model_name='gpt-4',
        max_tokens=500,        
    )
    chatgp_chain = LLMChain(
        llm=openai_client,
        prompt=chat_prompt,
        verbose=True,
        memory=ConversationBufferWindowMemory(k=10),
    )
    
    reply = chatgp_chain.predict(user_input='Hello, I am a human.')


    # url = 'https://note.com/_404'
    # response = requests.get(url)
    # res_status = response.status_code
    # msg = {
    #     f"status_code: {str(res_status)}"
    # }
    # print(msg)

    # return {
    #     'statusCode': 200,
    #     'body': json.dumps(msg)
    # }

# if __name__ == '__main__':
#     lambda_handler('Local invoke', None)
