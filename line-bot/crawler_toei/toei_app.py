import os
import time
import json
import logging
import requests
import boto3
from datetime import datetime
from dateutil.relativedelta import relativedelta
# selenium included by Lambda Layer
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


logger = logging.getLogger()
logger.setLevel(logging.INFO)
os.environ['HOME'] = '/var/task'

image_ext = '.png'
image_lang = 'ja-JP'
image_path = '/tmp/'
ts = datetime.now().strftime('%Y-%m-%d_%H%M%S')
this_month = datetime.now().month
next_month = (datetime.now() + relativedelta(months=1)).month
wide = 800
height = 900
scroll_count = 1


class TOEIFavoritParks:
    def __init__(self):
        self.data = {
            'gifName0': 'Shinozaki_A',
            'gifName1': 'OshimaKomatugawa_A',
            'gifName2': 'HigashiShirahige',
            'gifName3': 'SarueOnshi',
            'gifName4': 'Shioiri',
            'gifName5': 'Kameido',
            'gifName6': 'Kiba',
            'gifName7': 'HigashiAyase',
            'gifName8': 'Ukima',
            'gifName9': 'OiFuto',
        }
    def list_key(self):
        return self.data.keys()
    def resolve_name(self, park_key):
        return self.data.get(park_key)


def upload_s3_public(image_f):
    s3 = boto3.client('s3')
    image_bucket = os.getenv('IMAGE_BUCKET')
    image_key = image_f.split('/tmp/')[-1]

    try:
        s3.upload_file(
            Filename=image_f,
            Bucket=image_bucket,
            Key='line-bot/' + image_key,
            ExtraArgs={"ContentType": "image/png"}
        )
        s3.put_object_acl(
            ACL='public-read',
            Bucket=image_bucket,
            Key='line-bot/' + image_key
        )
    except Exception as e:
        logger.error(e)

    print('OK')
    return f"https://{image_bucket}.s3-ap-northeast-1.amazonaws.com/line-bot/{image_key}"


def reply_img(event, reply_set):
    # reply_set: [[park_name, image_url] * n]
    ssm = boto3.client('ssm')

    REPLY_ENDPOINT = 'https://api.line.me/v2/bot/message/reply'
    res_ssm = ssm.get_parameter(
        Name='line_accecc_token',
        WithDecryption=True
    )
    access_token = res_ssm['Parameter']['Value']
    header = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + access_token
    }

    columns_data = []
    for reply in reply_set:
        park_name = reply[0]
        image_url = reply[1]
        column = {
            "title": park_name,
            "thumbnailImageUrl": image_url,
            "text": "お気に入りの公園",
            "actions": [
                {
                    "type": "uri",
                    "label": "大きい画像をみる",
                    "uri": image_url
                }
            ]
        }
        columns_data.append(column)

    logger.info(columns_data)

    send_img = {
        "replyToken": event['replyToken'],
#        "messages": [{
#            "type": "image",
#            "originalContentUrl": image_url,
#            "previewImageUrl": image_url,
#        }]
        "messages": [{
            "type": "template",
            "altText": "sports.metro.tokyo",
            "template": {
                "type": "carousel",
                "columns": columns_data
#                "columns": [
#                    {
#                        "thumbnailImageUrl": image_url,
#                        "title": park_name,
#                        "text": "お気に入りの公園",
#                        "actions": [
#                            {
#                                "type": "uri",
#                                "label": "大きい画像をみる",
#                                "uri": image_url
#                            }
#                        ]
#                    },
#                    .....
#                ]
            }
        }]
    }

    print(json.dumps(send_img))
    res = requests.post(REPLY_ENDPOINT, headers=header, data=json.dumps(send_img))

    logger.info(res.text)


def get_png(event, driver, url, wait_key):
    wait = WebDriverWait(driver, 5)

    driver.get(url)
    wait.until(EC.presence_of_element_located((By.NAME, wait_key)))

    # switch iframe
    driver.switch_to.frame('pawae1002')
    # click logon button
    # CSS Selector: body > table:nth-child(1) > tbody:nth-child(1) > tr:nth-child(2) > td:nth-child(1) > a:nth-child(1) > img:nth-child(1)
    logon = driver.find_elements_by_css_selector('table:nth-child(1) a > img')
    logon[0].click()

    ##Login Page##
    wait.until(EC.presence_of_element_located((By.NAME, 'userId')))
    userid = driver.find_element_by_name('userId')
    userid.send_keys('xxxxxxxx')
    xyz = driver.find_element_by_name('password')
    xyz.send_keys('yyyyyyyy')

    time.sleep(5)
    login = driver.find_elements_by_css_selector('tr:nth-child(2) > td > a > img')
    login[0].click()

    ##Reservation Menu##
    yoyaku = driver.find_element_by_css_selector('tr:nth-child(1) > td:nth-child(1) tr:nth-child(1) img')
    yoyaku.click()

    ##Search Menu##
    favorite = driver.find_element_by_css_selector('#disp > center:nth-child(1) > form:nth-child(1) > table:nth-child(4) > tbody:nth-child(1) > tr:nth-child(2) > td:nth-child(1) > a:nth-child(1) > img:nth-child(1)')
    favorite.click()

    ##Selection Menu##
    # monthGif{#}: This Month
    # table.tablelist:nth-child(7) > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(2) > a:nth-child(1) > img:nth-child(1)
    month_key = this_month
    if datetime.now().day >= 22:
        month_key = next_month
    month = driver.find_element_by_name(f"monthGif{month_key}")
    month.click()
    # weektype5: Saturday
    # table.tablelist:nth-child(7) > tbody:nth-child(2) > tr:nth-child(2) > td:nth-child(2) > a:nth-child(6) > img:nth-child(1)
    # weektype6: Sunday
    # table.tablelist:nth-child(7) > tbody:nth-child(2) > tr:nth-child(2) > td:nth-child(2) > a:nth-child(7) > img:nth-child(1)
    # weektype7: Holiday
    # table.tablelist:nth-child(7) > tbody:nth-child(2) > tr:nth-child(2) > td:nth-child(2) > a:nth-child(8) > img:nth-child(1)
    sat = driver.find_element_by_name('weektype5')
    sat.click()
    sun = driver.find_element_by_name('weektype6')
    sun.click()
    holiday = driver.find_element_by_name('weektype7')
    holiday.click()

    ## Using Class: TOEIFavoritParks
    parks_data = TOEIFavoritParks()
    parks = parks_data.list_key()

    reply_set = []
    for park_key in parks:
        park = driver.find_element_by_name(park_key)
        park.click()

        # Search Button
        search = driver.find_element_by_css_selector('#disp > center:nth-child(1) > form:nth-child(1) > table:nth-child(8) > tbody:nth-child(1) > tr:nth-child(1) > td:nth-child(1) > a:nth-child(1) > img:nth-child(1)')
        search.click()

        park_name = parks_data.resolve_name(park_key)
        image_f = f"{image_path}{ts}_{park_name}{image_ext}"
        driver.save_screenshot(image_f)

        ## Upload .png to S3 for public content
        image_url = upload_s3_public(image_f)
        
        reply_set.extend([[park_name, image_url]])
        ## Reply Line
#        reply_img(event, park_name, image_url)
        
        # Back Button
        back = driver.find_element_by_css_selector('.head2 > tbody:nth-child(1) > tr:nth-child(2) > td:nth-child(1) > table:nth-child(1) > tbody:nth-child(1) > tr:nth-child(1) > td:nth-child(2) > a:nth-child(1) > img:nth-child(1)')
        back.click()

    ## Reply Line Message with .png
    reply_img(event, reply_set)

    body = f"Title: {driver.title}" 
    res = {
        "statusCode": 200,
        "body": body
    }

    driver.close()
    driver.quit()

    return res


def lambda_handler(event, context):
    logger.info(json.dumps(
        event,
        indent=4,
        ensure_ascii=False,
        ))
    options = webdriver.ChromeOptions()
    options.binary_location = '/opt/headless-chromium'
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument(f"--window-size={wide},{height}")
    options.add_argument("--hide-scrollbars")
    options.add_argument("--enable-logging")
    options.add_argument('--single-process')
    options.add_argument("--disable-application-cache")
    options.add_argument("--disable-infobars")
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument("--ignore-certificate-errors")

    driver = webdriver.Chrome('/opt/chromedriver', chrome_options=options)
    url = 'https://yoyaku.sports.metro.tokyo.lg.jp/web/index.jsp'

    wait_key = 'pawae1002'
    res = get_png(event, driver, url, wait_key)

    print(json.dumps(
        res,
        indent=2,
        ensure_ascii=False
        ))
