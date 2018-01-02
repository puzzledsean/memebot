import os
import time
import re
from slackclient import SlackClient

BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
BOT_ID = os.environ.get('SLACK_BOT_ID')

# instantiate slack client
slack_client = SlackClient(BOT_TOKEN)

# constants
RTM_READ_DELAY = 1   # 1 second delay between reading from RTM
AT_BOT = '<@' + BOT_ID + '>'
KEYWORDS = ['memes', 'meme', 'dank', 'shitposting']

def parse_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.

        If a command directed @memebot is found, this function returns a tuple of the commands and channel.
        If it's not found, then this function returns None, None.
    """

    for event in slack_events:
        # if found a message
        if event["type"] == "message" and not "subtype" in event:
            # get user commands
            commands = event['text'].split()
            targeted_bot = commands[0]
            
            # if user is @'ing the bot, return the commands/channel bot was called in
            if targeted_bot == AT_BOT:
                return commands[1:], event["channel"]

    return None, None

def handle_command(command, channel):
    """
        Posts a meme if user mentions one of the keywords. 
    """

    # Default response 
    default_response = 'No memes no dreams'

    # Finds and executes the given command, filling in response
    response = None
    user_command_str = ' '.join(command)

    # see if user mentioned any of the key responses 
    if any(keyword in user_command_str for keyword in KEYWORDS):
        response = "Sure...write some more code then I can do that!"

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )

def listen():
    '''
        Listens to Slack for events every RTM_READ_DELAY interval 
    '''
    
    if slack_client.rtm_connect(with_team_state=False):
        print("Meme Bot connected and running!")
        
        while True:
            command, channel = parse_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")

if __name__ == "__main__":
    listen()
