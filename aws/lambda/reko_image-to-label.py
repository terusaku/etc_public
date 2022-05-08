import json
import boto3
import urllib.parse

rek = boto3.client('rekognition')
s3c = boto3.client('s3')
s3r = boto3.resource('s3')
sns = boto3.client('sns')


def post_slack(msg):
    send_data = {
        "username": "ssm-session_end",
        "text": msg,
    }
    send_text = "payload=" + json.dumps(send_data)

    request = urllib.request.Request(
        "https://hooks.slack.com/services.....",
        data=send_text.encode("utf-8"), 
        method="POST"
    )
    
    with urllib.request.urlopen(request) as response:
        response_body = response.read().decode("utf-8")


def notice(labels):
    topic = 'arn:aws:sns:ap-northeast-1:AccountId:xxxxx'
    subject = '[Recognition Image to label]'
    
    msg = labels

    mail = {'TopicArn': topic ,'Message':  msg,'Subject': subject}
    sns.publish(**mail)

#    post_slack(msg)


def lambda_handler(event, context):
    
    threshold = 75
    output_bucket = 'lake-stat'

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')

    res_rek = rek.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':key}})
    print('Detecting labels for ' + key)

    records = ''
    header = 'filename' + ',' + 'Label-Name' + ',' + 'Confidence' + ',' + 'Parent-Category_1' + ',' + 'Parent-Category_2' + ',' + 'Parent-Category_3' + '\n'
    for l in res_rek['Labels']:
        label = []
        if (l['Confidence'] >= threshold):
            name = l['Name']
            value = str(l['Confidence'])

            label.append(key)
            label.append(name)
            label.append(value)

            if (len(l['Parents']) > 0):
                for i in range(len(l['Parents'])):
                    label.append(l['Parents'][i]['Name'])

        records = records + ','.join(map(str, label)) + '\n'
        
    labels = header + records
    print(labels)

    notice(labels)

