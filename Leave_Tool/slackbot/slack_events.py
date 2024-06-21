# slackbot/slack_events.py
from slack_bolt import App
from slack_bolt.adapter.django import SlackRequestHandler
from django.conf import settings

SLACK_BOT_TOKEN = settings.SLACK_BOT_TOKEN
SLACK_APP_TOKEN = settings.SLACK_APP_TOKEN

app = App(token=SLACK_BOT_TOKEN, name="Hw Bot")

@app.event("app_home_opened")
def say_hw(event, say):
    say("hello world")

slack_handler = SlackRequestHandler(app)