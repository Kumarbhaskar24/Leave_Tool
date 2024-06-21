import json
import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from slack_sdk.errors import SlackApiError
from .views import construct_view_blocks
from slack_sdk import WebClient
from threading import Thread
from ..utils.slack_utils import open_apply_modal, send_leave_history_image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = WebClient(token=settings.SLACK_BOT_TOKEN)

def handle_home_events(request):
    """
    This function manages the display of the home tab in the app.
    """
    try:
        event_data = json.loads(request.body.decode('utf-8'))
        logger.debug(f"Received event data: {event_data}")

        if 'type' in event_data and event_data['type'] == 'url_verification':
            return JsonResponse({'challenge': event_data['challenge']})

        if 'event' in event_data:
            event = event_data['event']

            if event['type'] == 'app_home_opened':
                user_id = event['user']
                channel_id = event['channel']
                logger.debug(f"Handling app_home_opened event for user: {user_id}")

                try:
                    view_payload = {
                        "type": "home",
                        "blocks": construct_view_blocks(True),
                        "private_metadata": channel_id,
                    }
                    result = client.views_publish(
                        user_id=user_id,
                        view=view_payload
                    )
                    logger.debug(f"Home view published successfully for user: {user_id}")
                except SlackApiError as e:
                    logger.error(f"Error publishing view: {e.response['error']}")
                    return HttpResponse(status=500)

                return HttpResponse(status=200)
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        return HttpResponse(status=500)

    logger.debug("Invalid request method or data")
    return HttpResponse(status=400)

def slack_slash_events(request):
    """
    Used to manage all the different types of slack events.
    """
    if request.method == 'POST':
        data = request.POST
        command = data.get('command')
        trigger_id = data.get('trigger_id')
        user_id = data.get('user_id')
        channel_id = data.get('channel_id')
        if command == '/apply':
            Thread(target=open_apply_modal, args=(trigger_id, user_id)).start()
            return HttpResponse(status=200)

        elif command == '/leavehistory':
            Thread(target=send_leave_history_image, args=(user_id, channel_id,trigger_id)).start()
            return HttpResponse(status=200)
    return HttpResponse(status=400)
