import boto3
import csv
import json
from datetime import datetime as d
 
inspec = boto3.client('inspector')
s3 = boto3.client('s3')
s3r = boto3.resource('s3')
sns = boto3.client('sns')

topic = 'arn:aws:sns:ap-northeast-1:~'
subject = '[Amazon Inspector] Monthly report'
 
BUCKET = '~'
 
base_line = 7
 
def mailing(f_name):
    presigne = s3.generate_presigned_url(
        ClientMethod = 'get_object',
        Params = {'Bucket' : BUCKET, 'Key' : f_name},
        ExpiresIn = 604800, # unit: second
        HttpMethod = 'GET')
 
    s3r.Object(BUCKET,f_name).download_file('/tmp/tmp3.csv')
 
    with open('/tmp/tmp3.csv') as f:
        reader = csv.reader(f)
        next(reader)
 
        host = ''
        score = 0
        desc = ''
        msg = ''
        message = ''
        count = 0
        no_count = 0
 
        for row in reader:
            host = row[0]
            score = float(row[1])
            desc = row[2]
 
            if score >= base_line:
                count += 1
            elif score < base_line:
                no_count += 1
 
        message = '''
Severity %i 以上は%iあります.
Severity %i 未満は%iあります.
下記リンクから詳細情報を確認してください.
''' % (base_line,count,base_line,no_count)
 
    mail = {'TopicArn': topic ,'Message':  message + presigne,'Subject': subject}
    sns.publish(**mail)
 
 
def lambda_handler(event, context):
 
    print(event)
    event_m = json.loads(event['Records'][0]['Sns']['Message'])
    print(event_m['run'])
    run_ARN = event_m['run']
 
    next_t = {}
    while True:
        res = inspec.list_findings(
            assessmentRunArns=[
                run_ARN
            ],
            maxResults=500,
            **next_t
        )
 
        finds = res['findingArns']
 
        rows = []
        for i in finds:
            find = {}
            find = inspec.describe_findings(
                findingArns=[
                    i,
                ],
                locale='EN_US'
            )['findings']
 
            for f in find:
                host = f['assetAttributes']['hostname']
#                score = f['attributes'][0].get('value')
                score = f['numericSeverity']
                title = f['title']
                desc = f['description']
                comment = f['recommendation']
 
                row = [host,score,title,desc,comment]
                rows.append(row)
 
        with open('/tmp/tmp.csv','a',newline='') as f:
            cw = csv.writer(f, delimiter=',')
            cw.writerows(rows)
 
        if 'nextToken' in res:
            next_t['nextToken'] = res['nextToken']
        else:
            break
 
 
    head = ['hostname','value','title','description','recommendation']
    with open("/tmp/tmp.csv") as rf, open("/tmp/tmptmp.csv","w",newline='') as wf:
        cr = csv.reader(rf)
        cw = csv.writer(wf)
        cw.writerow(head)
        cw.writerows(cr)
 
    now = d.now()
    now_str = now.strftime('%Y-%m-%d-%H%M%S')
    f_name = 'inspector' + '/' + now_str + '.csv'
 
    s3.upload_file('/tmp/tmptmp.csv', BUCKET, f_name)
 
    mailing(f_name)