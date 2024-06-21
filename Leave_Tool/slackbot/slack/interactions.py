import json
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from threading import Thread
from slack_sdk.errors import SlackApiError
from .views import disable_buttons
from ..utils.notification import send_notification, remove_buttons
from ..models import LeaveBalance, LeaveHistory
from ..utils.slack_utils import open_apply_modal, send_leave_history_image
from slack_sdk import WebClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
client = WebClient(token=settings.SLACK_BOT_TOKEN)

def handle_slack_interactions(request):
    payload = json.loads(request.POST['payload'])
    if payload['type'] == 'view_submission' and payload['view']['callback_id'] == 'apply_leave':
        return handle_apply_leave_submission(payload)
    elif payload['type'] == 'block_actions':
        return handle_block_actions(payload)
    return JsonResponse({'status': 'slack_interaction OK'})

def handle_apply_leave_submission(payload):
    user_id = payload['view']['private_metadata']
    response = client.users_info(user=user_id)
    user_info = response['user']
    display_name = user_info['profile'].get('real_name')
    form_data = {
        'name': display_name,
        'leave_type': payload['view']['state']['values']['leave_type_block']['leave_type']['selected_option']['value'],
        'description': payload['view']['state']['values']['description_block']['description']['value'],
        'start_date': payload['view']['state']['values']['start_date_block']['start_date']['selected_date'],
        'end_date': payload['view']['state']['values']['end_date_block']['end_date']['selected_date'],
    }

    try:
        employee = LeaveBalance.objects.get(employee_id=user_id)
    except LeaveBalance.DoesNotExist:
        send_notification(user_id, "Sorry, we don't have your data. Connect to the administration")
        return JsonResponse({'response_action': 'clear'})

    leave_type = form_data['leave_type']
    leave_balance = getattr(employee, leave_type)
    manager = employee.manager
    manager_id = manager.employee_id
    start_date = datetime.strptime(form_data['start_date'], '%Y-%m-%d')
    end_date = datetime.strptime(form_data['end_date'], '%Y-%m-%d')

    if start_date > end_date:
        send_notification(user_id, "You are choosing dates that are not valid for applying leaves.")
        return JsonResponse({'response_action': 'clear'})

    leave_count_required = 0
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() < 5: 
            leave_count_required += 1
        current_date += timedelta(days=1)
    
    if leave_balance < leave_count_required:
        send_notification(user_id, "Sorry, you have insufficient leave balance for the requested duration.")
        return JsonResponse({'response_action': 'clear'})

    if leave_count_required == 0:
        send_notification(user_id, "You are choosing dates that are not valid for applying leaves.")
        return JsonResponse({'response_action': 'clear'})

    send_notification(user_id, form_data, manager_id)
    send_notification(user_id, f"Your leave application has been submitted successfully:\nName: {form_data['name']}\nDescription: {form_data['description']}\nStart Date: {form_data['start_date']}\nEnd Date: {form_data['end_date']}")

    return JsonResponse({'response_action': 'clear'})

def handle_block_actions(payload):
    action_id = payload['actions'][0]['action_id']
    if action_id in ['accept_button', 'reject_button']:
        handle_leave_application_action(payload)
    elif action_id == 'leave_history_button':
        user_id = payload['user']['id']
        view_id = payload['view']['id']
        trigger_id = payload['trigger_id']
        channel_id = payload['view']['private_metadata']
        disable_buttons(view_id, channel_id)
        Thread(target=send_leave_history_image, args=(user_id, channel_id, trigger_id)).start()
    elif action_id == 'apply_leave_button':
        trigger_id = payload['trigger_id']
        user_id = payload['user']['id']
        Thread(target=open_apply_modal, args=(trigger_id, user_id)).start()
        return HttpResponse(status=200)
    return JsonResponse({'status': 'slack_interaction OK'})

def handle_leave_application_action(payload):
    channel_id = payload['channel']['id']
    message_ts = payload['message']['ts']
    button_value = json.loads(payload['actions'][0]['value'])
    user_id = button_value['user_id']
    start_date = button_value['start_date']
    end_date = button_value['end_date']
    leave_type = button_value['leave_type']

    form_data = {
        'start_date': start_date,
        'end_date': end_date,
        'leave_type': leave_type
    }

    if payload['actions'][0]['action_id'] == 'accept_button':
        leave_count_required = (datetime.strptime(form_data['end_date'], '%Y-%m-%d') - datetime.strptime(form_data['start_date'], '%Y-%m-%d')).days + 1
        if leave_count_required is not None:
            employee = LeaveBalance.objects.get(employee_id=user_id)
            leave_balance = getattr(employee, leave_type)
            new_leave_balance = leave_balance - leave_count_required
            setattr(employee, leave_type, new_leave_balance)
            employee.save()

            LeaveHistory.objects.create(
                employee=employee,
                type_of_leave=leave_type,
                start_date=form_data['start_date'],
                end_date=form_data['end_date'],
                leave_count=leave_count_required,
                leave_balance=new_leave_balance
            )

            send_notification(user_id, f"Your leave application has been accepted. Your pending {leave_type.replace('_', ' ')} balance is {new_leave_balance}.")
            remove_buttons(channel_id, message_ts, "The leave application has been accepted")
    elif payload['actions'][0]['action_id'] == 'reject_button':
        employee = LeaveBalance.objects.get(employee_id=user_id)
        leave_balance = getattr(employee, leave_type)
        send_notification(user_id, f"Your leave application has been rejected. Your pending {leave_type.replace('_', ' ')} balance is {leave_balance}.")
        remove_buttons(channel_id, message_ts, "The leave application has been rejected")
