import logging

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from django.conf import settings

# Logger 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = WebClient(token=settings.SLACK_BOT_TOKEN)

def construct_view_blocks(enable=False):
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Hello Everyone :wave:" if enable else "Hello :wave:"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Great to see you here! This app serves as your personal assistant for managing and applying leaves directly within Slack. Here's what you can do:" if enable else "Great to see you here! Please wait while your request is being processed."
            }
        }
    ]

    if enable:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "• Easily submit leave requests. \n • Access and review your leave history."
            }
        })
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "To use these features you have to use slash command that are: \n • /apply --> Use this for applying a leave\n • /leavehistory --> Use this to see your leave history"
            }
        })

    elements = [
        {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "Apply Leave"
            },
            "action_id": "apply_leave_button"
        },
        {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "Leave History"
            },
            "action_id": "leave_history_button"
        }
    ]

    if not enable:
        for element in elements:
            element["style"] = "danger"
            element["confirm"] = {
                "title": {
                    "type": "plain_text",
                    "text": "Processing"
                },
                "text": {
                    "type": "mrkdwn",
                    "text": "Please wait while your request is being processed."
                },
                "confirm": {
                    "type": "plain_text",
                    "text": "OK"
                }
            }

    blocks.append({
        "type": "actions",
        "elements": elements
    })

    return blocks

def update_view(id, blocks,enable=True):
    try:
        if enable:
            response = client.views_publish(
                user_id=id, 
                view={
                    "type":"home",
                    "blocks":blocks
                })
        else:
            response = client.views_update(
                view_id=id, 
                view={
                    "type":"home",
                    "blocks":blocks
                })
    except SlackApiError as e:
        logger.error(f"Error updating view: {e.response['error']}")

def enable_buttons(user_id, channel_id):
    try:
        blocks = construct_view_blocks(True)
        update_view(user_id, blocks,True)
    except SlackApiError as e:
        logger.error(f"Error enabling buttons: {e.response['error']}")

def disable_buttons(view_id, channel_id):
    try:
        blocks = construct_view_blocks(False)
        update_view(view_id, blocks,False)
    except SlackApiError as e:
        logger.error(f"Error disabling buttons: {e.response['error']}")
