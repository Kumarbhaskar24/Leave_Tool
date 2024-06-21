from django.urls import path
from . import views

urlpatterns = [
    path('apply/leave', views.slack_events, name='slack_events'),
    path('slack/interactions', views.slack_interactions, name='slack_interactions'),
    path('leave/history', views.slack_events, name='slack_events'),
    path('slack/event', views.app_home_handler, name='app_home_handler'),
]
