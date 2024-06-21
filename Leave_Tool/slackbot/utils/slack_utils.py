import logging
import imgkit
import io
import logging

from django.template.loader import render_to_string
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from ..models import LeaveBalance, LeaveHistory
from ..slack.views import enable_buttons
from ..utils.notification import send_notification
from django.conf import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = WebClient(token=settings.SLACK_BOT_TOKEN)

def open_apply_modal(trigger_id, user_id):
    """
    Open a Slack modal for applying leave.
    
    Args:
    - trigger_id: The trigger ID from the Slack command.
    - user_id: The Slack user ID of the user applying for leave.
    
    Returns:
    - None
    """
    modal = {
        "type": "modal",
        "callback_id": "apply_leave",
        "title": {
            "type": "plain_text",
            "text": "Apply for Leave"
        },
        "blocks": [
            {
                "type": "input",
                "block_id": "description_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "description"
                },
                "label": {
                    "type": "plain_text",
                    "text": "Short Description"
                }
            },
            {
                "type": "input",
                "block_id": "leave_type_block",
                "element": {
                    "type": "static_select",
                    "action_id": "leave_type",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a leave type"
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Sick Leave"
                            },
                            "value": "sick_leave"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Paid Leave"
                            },
                            "value": "paid_leave"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Unpaid Leave"
                            },
                            "value": "unpaid_leave"
                        }
                    ]
                },
                "label": {
                    "type": "plain_text",
                    "text": "Type of Leave"
                }
            },
            {
                "type": "input",
                "block_id": "start_date_block",
                "element": {
                    "type": "datepicker",
                    "action_id": "start_date"
                },
                "label": {
                    "type": "plain_text",
                    "text": "Start Date"
                }
            },
            {
                "type": "input",
                "block_id": "end_date_block",
                "element": {
                    "type": "datepicker",
                    "action_id": "end_date"
                },
                "label": {
                    "type": "plain_text",
                    "text": "End Date"
                }
            }
        ],
        "submit": {
            "type": "plain_text",
            "text": "Submit"
        },
        "private_metadata": user_id
    }

    try:
        response = client.views_open(
            trigger_id=trigger_id,
            view=modal
        )
        logger.info(f"Modal opened: {response['view']['id']}")
    except SlackApiError as e:
        logger.error(f"Failed to open modal: {e.response['error']}")

def html_to_image(html_content):
    """
    Used to convert html to image format
    """
    options = {
        'format': 'png',
        'width': '1024', 
    }
    imgkit_output = imgkit.from_string(html_content, False, options=options)
    return io.BytesIO(imgkit_output)

def send_leave_history_image(user_id, channel_id,trigger_id):
    """
    This function retrieves the leave history for a specified user and 
    sends an image of this history as a notification 
    """
    try:
        employee = LeaveBalance.objects.get(employee_id=user_id)
    except LeaveBalance.DoesNotExist:
        send_notification(user_id, "No leave balance found.")
        logger.info("No leave balance found.")
        return

    leave_history_records = LeaveHistory.objects.filter(employee=employee)
    if not leave_history_records.exists():
        send_notification(user_id, "No leave history found.")
        logger.info("No leave history found.")
        return

    leave_history_data = [
        {
            'type_of_leave': record.type_of_leave,
            'start_date': record.start_date,
            'end_date': record.end_date,
            'leave_count': record.leave_count,
            'leave_balance': record.leave_balance
        }
        for record in leave_history_records
    ]

    html_content = render_to_string('slackbot/leave_history_template.html', {'leave_history': leave_history_data})
    image_data = html_to_image(html_content)
    try:
        response = client.files_upload_v2(
            channel=channel_id,
            initial_comment="Here's your leave history:",
            file=image_data,
            filename='leave_history.png'
        )
    except SlackApiError as e:
        logger.error(f"Error uploading leave history: {e.response['error']}")
    enable_buttons(user_id,channel_id)
