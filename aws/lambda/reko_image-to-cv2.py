import os
import json
import boto3
import cv2
import urllib.parse


def lambda_handler(event, content):
    
    print(json.dumps(event))
    
    s3 = boto3.client('s3')
    reko = boto3.client('rekognition')

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    input_file = key.split('/')[-1]

    print('Detecting labels for ' + input_file)

    tmp_dir = '/tmp/'
    input_f = tmp_dir + input_file
    output_path = 'result/cv2_'

    with open(input_f, 'wb') as data:
        s3.download_fileobj(bucket, key, data)

    image = cv2.imread(input_f)
    height, width = image.shape[:2]

    res_reko = reko.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':key}})

#    print(json.dumps(res_reko))
    l_count = 0
    for label in res_reko['Labels']:
        if len(label['Instances']) == 0:
            continue
#        if len(res_reko['Labels'][x]['Instances']) == 0:
#        if res_reko['Labels'][x]['Instances']['BoundingBox'] not in ['People', 'Person', 'Human']:
        else:
            l_count += 1
            box = label['Instances'][0]['BoundingBox']
            x = round(width * box['Left'])
            y = round(height * box['Top'])
            w = round(width * box['Width'])
            h = round(height * box['Height'])

        cv2.rectangle(image, (x, y), (x + w, y + h), (255, 255, 255), 3)
        cv2.putText(image, label['Name'], (x, y - 4),
        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        cv2.imwrite(input_f, image)
#        cv2.imwrite(output_f, image)

#        for person in res_reko['Labels'][x]['Instances']:
#            box = person['BoundingBox']
#            x = round(width * box['Left'])
#            y = round(height * box['Top'])
#            w = round(width * box['Width'])
#            h = round(height * box['Height'])
#            cv2.rectangle(image, (x, y), (x + w, y + h), (255, 255, 255), 3)
#            cv2.putText(image, label['Name'], (x, y - 4),
#                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
    
    if l_count == 0:
        output_file = output_path + 'nothing_' + input_file
    else:
        output_file = output_path + input_file
        
    # S3に描画後の画像をアップロードする
#    s3.Bucket(bucket).upload_file(output_f, 'result/cv2_' + input_file)
    with open(input_f, 'rb') as data:
        s3.upload_fileobj(data, bucket, output_file)

    os.remove(input_f)
#    os.remove(output_f)
