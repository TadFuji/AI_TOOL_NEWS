import os
import sys
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage,
)

def send_failure_alert():
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.environ.get("LINE_USER_ID")
    
    if not token or not user_id:
        print("Error: Missing LINE credentials for alert.")
        return

    # Error details from Github Actions (if available via env)
    workflow_name = os.environ.get("GITHUB_WORKFLOW", "News Update")
    repo_name = os.environ.get("GITHUB_REPOSITORY", "Unknown Repo")
    job_url = f"https://github.com/{repo_name}/actions"

    alert_msg = (
        f"⚠️ 【緊急速報】システム停止警報\n\n"
        f"クラウド上の自動更新プログラム({workflow_name})でエラーが発生しました。\n"
        f"ニュース収集が停止している可能性があります。\n\n"
        f"▼ 確認してください:\n{job_url}"
    )

    configuration = Configuration(access_token=token)
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            push_message_request = PushMessageRequest(
                to=user_id,
                messages=[TextMessage(text=alert_msg)]
            )
            line_bot_api.push_message(push_message_request)
            print("🚨 Failure alert sent to LINE.")
    except Exception as e:
        print(f"Failed to send alert: {e}")

if __name__ == "__main__":
    send_failure_alert()
