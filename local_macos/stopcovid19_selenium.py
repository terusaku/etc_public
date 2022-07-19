import os
import json
import shutil
import zipfile
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from requests_oauthlib import OAuth1Session


image_name = 'test.png'
image_lang = 'ja-JP'
image_path = './image/'
image_key = datetime.now().strftime('%Y-%m-%d_%H%M%S')
height = 1500
scroll_count = 3


def post_slack(image_f):
    ch = '' #Slack Channel Id
    b_token = '' # Slack Bot Token
    api_s_upload = 'https://slack.com/api/files.upload'

    image = {'file': open(image_f, 'rb')}
    params = {
        'token': b_token,
        'channels': ch,
    }
    res_slack = requests.post(url=api_s_upload, params=params, files=image)

    return res_slack


def post_twitter(image_f,url_title,find_text,num):
    CK = '' #Consumer Key
    CS = '' #Consumer Key Secret
    AT = '' #OAuth Token
    AS = '' #OAuth Token Secret
    twitter = OAuth1Session(CK,CS,AT,AS)

    api_tw_upload = 'https://upload.twitter.com/1.1/media/upload.json'
    api_tw_text = 'https://api.twitter.com/1.1/statuses/update.json'

    image = {"media" : open(image_f, 'rb')}
    req_media = twitter.post(api_tw_upload, files=image)
    media_id = json.loads(req_media.text)['media_id_string']

    number = str(int(num)+1)
    msg = f'''
'''
    data = {"status": msg, "media_ids": media_id}
    twitter.post(api_tw_text, params=data)


def get_png(url,wait_key):
    driver.get(url)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, wait_key)))
    find_elem = driver.find_element_by_class_name(wait_key)
    graph = driver.find_element_by_class_name('SideNavigation-Body')
    check = graph.is_displayed()
    
    n = 0
    while n < scroll_count:
        scroll_h = height * n * 0.9
        image_f = image_path + image_key + '_' + str(n) + '_' + image_name

        driver.execute_script(f"window.scrollTo(0, {scroll_h});")
        driver.save_screenshot(image_f)
        post_slack(image_f)
        post_twitter(image_f,driver.title,find_elem.text,str(n))
        n += 1

    body = f"Title: {driver.title}, {wait_key}: {find_elem.text}, is_displayed: {check}" 
    res = {
        "statusCode": 200,
        "body": body
    }
    
    driver.close();
    driver.quit();

    return res


def get_latest_driver():
    today = datetime.now().strftime('%Y%m%d')
    
    res = requests.get('https://chromedriver.storage.googleapis.com/LATEST_RELEASE')
    latest = res.text
    driver_url = f"https://chromedriver.storage.googleapis.com/{latest}/chromedriver_mac64.zip"

    shutil.copy(driver_f, f"{driver_f}_{today}")
    
    res = requests.get(driver_url)
    with open(f"{driver_f}_{latest}.zip", 'wb') as f:
        f.write(res.content)
    
    with zipfile.ZipFile(f"{driver_f}_{latest}.zip") as zipf:
        zipf.extract('chromedriver')
    
    os.remove(f"{driver_f}_{latest}.zip")


driver_f = './chromedriver'
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument(f"--lang={image_lang}")
options.add_argument(f"--window-size=1600,{height}")
options.add_argument("--enable-logging")
options.add_argument("--disable-application-cache")
options.add_argument("--disable-infobars")
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument("--ignore-certificate-errors")

url = 'https://stopcovid19.metro.tokyo.lg.jp/'
wait_key = 'UpdatedAt'

try:
    driver = webdriver.Chrome(driver_f, options=options)
except Exception as e:
    get_latest_driver()
    driver = webdriver.Chrome(driver_f, options=options)

wait = WebDriverWait(driver, 30)

res = get_png(url,wait_key)

print(json.dumps(
    res,
    indent=2,
    ensure_ascii=False
    ))
