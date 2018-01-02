import os
import time
import re
from slackclient import SlackClient

BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
print(BOT_TOKEN)
slack_client = SlackClient(BOT_TOKEN)
