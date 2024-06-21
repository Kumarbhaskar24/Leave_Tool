from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .slack.events import handle_home_events, slack_slash_events
from .slack.interactions import handle_slack_interactions

@csrf_exempt
def app_home_handler(request):
    """
    This function manages the display of the home tab in the app.
    """
    if request.method == 'POST':
        return handle_home_events(request)
    return HttpResponse(status=400)

@csrf_exempt
def slack_events(request):
    """
    This function is responsible to handle all types slash events that will be fired.
    """
    if request.method == 'POST':
        return slack_slash_events(request)
    return HttpResponse(status=400)

@csrf_exempt
def slack_interactions(request):
    """
    This function is responsible to handle all the interation from the slack UI.
    """
    if request.method == 'POST':
        return handle_slack_interactions(request)
    return JsonResponse({'status': 'slack_interaction OK'})
