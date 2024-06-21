import logging
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from django.conf import settings

logger = logging.getLogger(__name__)

client = WebClient(token=settings.SLACK_BOT_TOKEN)

def send_notification(user_id, data, manager_id=None):
    try:
        if manager_id:
            response = client.chat_postMessage(
                channel=manager_id,
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"You have a new leave request from <@{user_id}>:\n*Description:* {data['description']}\n*Start Date:* {data['start_date']}\n*End Date:* {data['end_date']}"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Accept"
                                },
                                "style": "primary",
                                "action_id": "accept_button",
                                "value": json.dumps({
                                    "user_id": user_id,
                                    "start_date": data['start_date'],
                                    "end_date": data['end_date'],
                                    "leave_type": data['leave_type']
                                })
                            },
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Reject"
                                },
                                "style": "danger",
                                "action_id": "reject_button",
                                "value": json.dumps({
                                    "user_id": user_id,
                                    "start_date": data['start_date'],
                                    "end_date": data['end_date'],
                                    "leave_type": data['leave_type']
                                })
                            }
                        ]
                    }
                ]
            )
        else:
            response = client.chat_postMessage(
                channel=user_id,
                text= data
            )
        return response
    except SlackApiError as e:
        logger.error(f"Error sending notification: {e.response['error']}")
        return None

def remove_buttons(channel_id, message_ts, text):
    try:
        client.chat_update(
            channel=channel_id,
            ts=message_ts,
            text=text,
            blocks=[]
        )
    except SlackApiError as e:
        logger.error(f"Error removing buttons: {e.response['error']}")

def send_slack_message(channel, text, blocks=None):
    try:
        response = client.chat_postMessage(
            channel=channel,
            text=text,
            blocks=blocks
        )
        return response
    except SlackApiError as e:
        logger.error(f"Error sending message: {e.response['error']}")
        return None
