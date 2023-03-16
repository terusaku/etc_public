import os
import json
import logging
import requests
import boto3
from datetime import datetime
from dateutil.relativedelta import relativedelta
# selenium included by Lambda Layer
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select 
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException, NoSuchElementException


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
height = 2000
scroll_count = 1

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
            "text": "日別空き状況",
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
            "altText": "city.kita.tokyo",
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

    # Operation Mode
    start_ope = driver.find_elements_by_css_selector('.second > dl:nth-child(1) > dt:nth-child(1) > form:nth-child(1) > input:nth-child(2)')
    start_ope[0].click()

    Kakunin = driver.find_elements_by_css_selector('#local-navigation > dd:nth-child(2) > ul:nth-child(1) > li:nth-child(1) > a:nth-child(1)')
    Kakunin[0].click()

    Category1 = driver.find_elements_by_xpath("//option[@value='5001']")
    Category1[0].click()

    Category1_done = driver.find_elements_by_xpath("//input[@onclick='submitBunrui1();']")
    Category1_done[0].click()

    Category2 = driver.find_elements_by_xpath("//option[@value='5101']")
    Category2[0].click()
    Category2_done = driver.find_elements_by_xpath("//input[@onclick='submitBunrui2();']")
    Category2_done[0].click()

    # waiting Pull Down
    wait.until(EC.presence_of_element_located((By.NAME, 'riyosmk')))

    PullDown_List = driver.find_element_by_name('riyosmk')
    PullDown_Elem = Select(PullDown_List)
    PullDown_Elem.select_by_value('5000')
    PullDown_done = driver.find_elements_by_xpath("//input[@onclick='changed()']")
    PullDown_done[0].click()

    Facilities = driver.find_elements_by_xpath("//input[@onclick='buttonClick()']")
    Facilities[0].click()

    # Select all the elems in selection box
#def click_all_locations():
    LocationList = driver.find_element_by_name('g_basyocd')
    Locales = Select(LocationList).options
    actions = ActionChains(driver)
    actions.key_down(Keys.SHIFT)
    for loc in Locales:
        loc_value = loc.get_attribute('value')
        location = driver.find_elements_by_xpath(f"""//option[@value={loc_value}]""")
#        print(location[0].text)
#        actions.key_down(Keys.SHIFT)
        actions.click(location[0])
    actions.key_up(Keys.SHIFT)
    actions.perform()

    Location_done = driver.find_elements_by_xpath("//input[@onclick='btnOK_3()']")
    Location_done[0].click()

    # Select all the elems in selection box
#def click_all_Rooms():
    RoomList = driver.find_element_by_name('g_heyacd')
    Rooms = Select(RoomList).options
    print(len(Rooms))
#    driver_2 = webdriver.Chrome('/opt/chromedriver', chrome_options=options)
    actions_2 = ActionChains(driver)
    actions_2.key_down(Keys.SHIFT)
    for room in Rooms:
        room_value = room.get_attribute('value')
        room_elem = driver.find_elements_by_xpath(f"""//option[@value="{room_value}"]""")
        print(room_elem[0].text)
#        actions_2.key_down(Keys.SHIFT)
        actions_2.click(room_elem[0])
    actions_2.key_up(Keys.SHIFT)
    actions_2.perform()

#    time.sleep(5)

    Room_done = driver.find_elements_by_xpath("//input[@onclick='heyaOK();']")
    Room_done[0].click()


    Sunday = driver.find_elements_by_xpath("//input[@onclick='clickYobi(0)']")
    Sunday[0].click()
    Saturday = driver.find_elements_by_xpath("//input[@onclick='clickYobi(6)']")
    Saturday[0].click()
    Holiday = driver.find_elements_by_xpath("//input[@onclick='clickYobi(7)']")
    Holiday[0].click()


#    driver.execute_script(f"window.scrollTo(0, 0);")
#    driver.save_screenshot('/tmp/test.png')
#    test_image = upload_s3_public('/tmp/test.png')
#    print(test_image)


    # Start Search
    driver.find_element_by_id('btnOK').click()
#    display = driver.window_handles
#    print(display)
#    driver.switch_to.window(display[0])

    click_count = 9
    scroll_count = 1
    reply_set = []
    for page_n in range(click_count):
        image_key = datetime.now().strftime('%Y-%m-%d_%H%M%S')

        scroll_n = 0
        while scroll_n < scroll_count:
            scroll_h = height * scroll_n * 0.9
            wait.until(EC.presence_of_element_located((By.ID, 'contents')))
#            print(driver.find_elements_by_xpath("//h3/span"))
            page_date = driver.find_elements_by_xpath("//h3/span")[0].text
            image_f = f"{image_key}_p{page_n}-{scroll_n}.png"
            shot = image_path + image_f

            driver.execute_script(f"window.scrollTo(0, {scroll_h});")
            driver.save_screenshot(shot)

            image_url = upload_s3_public(shot)

            reply_set.extend([[f"{page_date}_p{page_n}-{scroll_n}", image_url]])
            print(f"Screenshot: PAGE{page_n}, {scroll_n}")
            scroll_n += 1
        else:
            try:
                driver.find_element_by_link_text('次へ').click()
#                next_page = driver.find_element_by_link_text('次へ')
#                next_page[0].click()
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

    # 東京都北区施設予約システム
    url = 'https://yoyaku.city.kita.tokyo.jp/shisetsu/reserve/gin_menu'
    wait_key = 'lang-nav'
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
