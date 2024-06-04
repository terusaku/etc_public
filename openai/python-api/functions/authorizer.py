import json
import os
import hmac
import hashlib

# 環境変数からSlackの署名秘密鍵を取得
SLACK_SIGNING_SECRET = os.environ['SLACK_SIGNING_SECRET']

def lambda_handler(event, context):
    # Slackからのリクエストの署名を検証
    if not verify_slack_signature(event):
        return {'statusCode': 401, 'body': 'Unauthorized'}
    
    # Slackからのイベントデータを取得
    slack_event = json.loads(event['body'])

    # URL検証イベントに応答する（Slack Appの初期設定時に必要）
    if "challenge" in slack_event:
        return {'statusCode': 200, 'body': json.dumps({'challenge': slack_event['challenge']})}

    return {'statusCode': 200, 'body': 'Success'}

def verify_slack_signature(event):
    # ヘッダから署名関連の値を取得
    slack_signature = event['headers']['X-Slack-Signature']
    slack_request_timestamp = event['headers']['X-Slack-Request-Timestamp']

    # 署名を構成する
    sig_basestring = f"v0:{slack_request_timestamp}:{event['body']}".encode('utf-8')
    my_signature = 'v0=' + hmac.new(
        SLACK_SIGNING_SECRET.encode('utf-8'),
        sig_basestring,
        hashlib.sha256
    ).hexdigest()

    # 署名が一致するか検証
    return hmac.compare_digest(my_signature, slack_signature)

# Lambda関数へのエントリポイント
if __name__ == "__main__":
    lambda_handler({'body': json.dumps({'challenge': 'test_challenge'})}, None)
