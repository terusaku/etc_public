import os
import json
import logging
import requests
import boto3
from datetime import datetime
from dateutil.relativedelta import relativedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, NoSuchElementException
#from bs4 import BeautifulSoup
#from requests_oauthlib import OAuth1Session


logger = logging.getLogger()
logger.setLevel(logging.INFO)
os.environ['HOME'] = '/var/task'

image_ext = '.png'
image_lang = 'ja-JP'
image_path = '/tmp/'
ts = datetime.now().strftime('%Y-%m-%d_%H%M%S')
this_month = datetime.now().month
next_month = (datetime.now() + relativedelta(months=1)).month
wide = 1400
height = 1200

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


#def get_latest_driver():
#    today = datetime.now().strftime('%Y%m%d')
#    
#    res = requests.get('https://chromedriver.storage.googleapis.com/LATEST_RELEASE')
#    latest = res.text
#    driver_url = f"https://chromedriver.storage.googleapis.com/{latest}/chromedriver_mac64.zip"
#
#    shutil.copy(driver_f, f"{driver_f}_{today}")
#    
#    res = requests.get(driver_url)
#    with open(f"{driver_f}_{latest}.zip", 'wb') as f:
#        f.write(res.content)
#    
#    with zipfile.ZipFile(f"{driver_f}_{latest}.zip") as zipf:
#        zipf.extract('chromedriver')
#    
#    os.remove(f"{driver_f}_{latest}.zip")


def upload_s3_public(image_f):
    s3 = boto3.client('s3')
    image_bucket = os.getenv('IMAGE_BUCKET')
    image_key = image_f.split(image_path)[-1]

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

#    print('OK')
    # https://lake-img-pub-ts.s3-ap-northeast-1.amazonaws.com/2020-07-14_105632_OshimaKomatugawa_A.png
    return f"https://{image_bucket}.s3-ap-northeast-1.amazonaws.com/line-bot/{image_key}"


def reply_img(event, reply_set):
    # reply_set: [[page_date, image_url] * n]
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
        page_name = reply[0]
        image_url = reply[1]
        column = {
            "thumbnailImageUrl": image_url,
            "title": page_name,
            "text": "台東区空き状況",
            "actions": [
                {
                    "type": "uri",
                    "label": "大きい画像をみる",
                    "uri": image_url
                }
            ]
        }
        columns_data.append(column)

#    logger.info(columns_data)

    send_img = {
        "replyToken": event['replyToken'],
#        "messages": [{
#            "type": "image",
#            "originalContentUrl": image_url,
#            "previewImageUrl": image_url,
#        }]
        "messages": [{
            "type": "template",
            "altText": "city.taito.tokyo",
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
    wait.until(EC.presence_of_element_located((By.ID, wait_key)))

    # Reservation Menu
    driver.find_element_by_id('btnNormal').click()    
    # Search availability
    driver.find_element_by_id('rbtnYoyaku').click()
    # How to search
    driver.find_element_by_id('btnMokuteki').click()
    # Sports
    driver.find_element_by_id('ucOecRadioButtonList_dgButtonList_ctl02_rdSelectRight').click()
    # Tennis
    driver.find_element_by_id('ucButtonList_dgButtonList_ctl07_chkSelectLeft').click()
    driver.find_element_by_id('ucPCFooter_btnForward').click()
    # waiting Next button
    wait.until(EC.presence_of_element_located((By.ID, 'ucPCFooter_btnForward')))
    # No Select at Facilities 
    driver.find_element_by_id('ucPCFooter_btnForward').click()
    # waiting Next button
    wait.until(EC.presence_of_element_located((By.ID, 'ucPCFooter_btnForward')))
    # Select Location
    ## RiverSide Tennis court
    driver.find_element_by_id('dgTable_ctl02_chkShisetsu').click()
    ## Ryuhoku Sports Pra
    driver.find_element_by_id('dgTable_ctl04_chkShisetsu').click()

    driver.find_element_by_id('ucPCFooter_btnForward').click()

    # Montyly
    driver.find_element_by_id('rbtnMonth').click()
    # Sat, Sun, Holiday
    driver.find_element_by_id('chkSat').click()
    driver.find_element_by_id('chkSun').click()
    driver.find_element_by_id('chkHol').click()

    driver.find_element_by_id('ucPCFooter_btnForward').click()
    # waiting Next button
    wait.until(EC.presence_of_element_located((By.ID, 'ucPCFooter_btnForward')))

    page_count = 2
    scroll_count = 1
    reply_set = []
    for page_n in range(page_count):
        image_key = datetime.now().strftime('%Y-%m-%d_%H%M%S')

        scroll_n = 0
        while scroll_n < scroll_count:
            scroll_h = height * scroll_n * 0.9
            image_f = f"{image_key}_p{page_n}-{scroll_n}.png"
            shot = image_path + image_f

            driver.execute_script(f"window.scrollTo(0, {scroll_h});")
            driver.save_screenshot(shot)

            image_url = upload_s3_public(shot)

            reply_set.extend([[f"Taito_Tennis_p{page_n}-{scroll_n}", image_url]])
            print(f"Screenshot: PAGE{page_n}, {scroll_n}")
            scroll_n += 1
        else:
            try:
                # Next Span
                driver.find_element_by_id('dlRepeat_ctl00_tpItem_Migrated_lnkNextSpan').click()
                # waiting Next button
                # wait.until(EC.presence_of_element_located((By.ID, 'ucPCFooter_btnForward')))
            except NoSuchElementException as e:
                logger.info(e)
            except WebDriverException as e:
                logger.error(e)
                raise e
            except Exception as e:
                logger.error(e)

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

#    n = 0
#    while n < scroll_count:
#        scroll_h = height * n * 0.9
#        image_f = image_path + ts + '_' + str(n) + '_' + image_ext
#
#        driver.execute_script(f"window.scrollTo(0, {scroll_h});")
#        driver.save_screenshot(image_f)
##        post_slack(image_f)
##        post_twitter(image_f,driver.title,find_elem.text,str(n))
#        n += 1

##    body = f"Title: {driver.title}, {wait_key}: {find_elem.text}" 


def lambda_handler(event, context):
    logger.info(json.dumps(
        event,
        indent=4,
        ensure_ascii=False,
        ))
#    options = webdriver.ChromeOptions()
#    options.binary_location = '/opt/headless-chromium'
#    options.add_argument('--headless')
#    options.add_argument('--no-sandbox')
#    options.add_argument(f"--window-size={wide},{height}")
#    options.add_argument("--hide-scrollbars")
#    options.add_argument("--enable-logging")
#    options.add_argument('--single-process')
#    options.add_argument("--disable-application-cache")
#    options.add_argument("--disable-infobars")
#    options.add_argument('--disable-dev-shm-usage')
#    options.add_argument('--disable-gpu')
#    options.add_argument("--ignore-certificate-errors")

    driver = webdriver.Chrome('/opt/chromedriver', chrome_options=options)

#    try:
#        driver = webdriver.Chrome(driver_f, options=options)
#    except Exception as e:
#        get_latest_driver()
#        driver = webdriver.Chrome(driver_f, options=options)

    # 東京都台東区施設予約システム
    url = 'https://shisetsu.city.taito.lg.jp'
    wait_key = 'btnNormal'
    res = get_png(event, driver, url, wait_key)

    print(json.dumps(
        res,
        indent=2,
        ensure_ascii=False
        ))

#    url = 'https://google.com'
#    driver.get(url)
#    body = f"Title: {driver.title}"
#    driver.save_screenshot('/tmp/test.png')
#    response = {
#        "statusCode": 200,
#        "body": body
#    }
#    s3 = boto3.client('s3')
#    s3.upload_file(
#        Filename="/tmp/test.png",
#        Bucket=os.getenv('IMAGE_BUCKET'),
#        Key="test.png") 
#    driver.close();
#    driver.quit();
#    return response
