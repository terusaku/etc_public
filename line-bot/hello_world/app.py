import os
import json
import logging
import requests
import boto3


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def gen_url(img_bucket, obj_key):
    s3 = boto3.client('s3')

    presigned_url = s3.generate_presigned_url(
        ClientMethod = 'get_object',
        Params = {'Bucket' : img_bucket, 'Key' : obj_key},
        ExpiresIn = 120, # unit: second
        HttpMethod = 'GET')
    
    return presigned_url


def lambda_handler(event, context):
#    logger.info(json.dumps(
#        event,
#        indent=4,
#        ensure_ascii=False,
#        ))
    
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    # try:
    #     ip = requests.get("http://checkip.amazonaws.com/")
    # except requests.RequestException as e:
    #     # Send some context about this error to Lambda Logs
    #     print(e)

    #     raise e
    
    client = boto3.client('lambda')

    if not 'body' in event:
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "hello world",
                # "location": ip.text.replace("\n", "")
            }),
        }

#    return {
#        "statusCode": 200,
#        "body": json.dumps({
#            "type": "text",
#            "text": "OK",
#        })
#    }

    else:
        if 'body' in event:
            line_req = json.loads(event['body'])
            line_event = line_req['events'][0]
            logger.info(json.dumps(
                line_event,
                indent=4,
                ensure_ascii=False,
            ))

            if line_event['replyToken'] == '00000000000000000000000000000000' or line_event['message']['text'] == 'Hello, world':
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "message": "hello world, too",
                        # "location": ip.text.replace("\n", "")
                    }),
                }

            if not line_event['message']['text'] in ['チェック', '都営', '北区', '台東区']: 
                return {
                    "statusCode": 400,
                    "message": "botキーワードに該当なし",
                }
            elif line_event['message']['text'] == '台東区':
                res = client.invoke(
                    FunctionName='sam-line-bot-CrawlerTaito',
                    InvocationType='Event',
                    LogType='Tail',
                    Payload= json.dumps(line_event)
                )
            elif line_event['message']['text'] == '北区':
                res = client.invoke(
                    FunctionName='sam-line-bot-CrawlerKita',
                    InvocationType='Event',
                    LogType='Tail',
                    Payload= json.dumps(line_event)
                )
            elif line_event['message']['text'] in ['チェック', '都営']:
                res = client.invoke(
                    FunctionName='sam-line-bot-CrawlerToei',
                    InvocationType='Event',
                    LogType='Tail',
                    Payload= json.dumps(line_event)
                )
                logger.info(res)
