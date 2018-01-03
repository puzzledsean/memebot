import os
import time
import random 
import requests
import praw

from slackclient import SlackClient

BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
BOT_ID = os.environ.get('SLACK_BOT_ID')

# instantiate reddit praw client
reddit = praw.Reddit(client_id=os.environ.get('REDDIT_CLIENT_ID'),
                    client_secret=os.environ.get('REDDIT_CLIENT_SECRET'), 
                    password=os.environ.get('REDDIT_PW'), 
                    username=os.environ.get('REDDIT_USER'),
                    user_agent='memebot')

# instantiate slack client
slack_client = SlackClient(BOT_TOKEN)

# constants
RTM_READ_DELAY = 1   # 1 second delay between reading from RTM
AT_BOT = '<@' + BOT_ID + '>'
KEYWORDS = ['memes', 'meme', 'dank', 'shitposting', 'shitpost', 'funny', 'meirl', 'me irl', 'me_irl']
SUBREDDITS = ['meirl', 'memes', 'funny']

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

    # Default response if user doesn't mention a keyword 
    default_response = random.choice([
        'No memes no dreams',
        'No memes for u',
        'Rest in peace Harambe',
        'How about no',
        'The earth is flat',
        ])

    # Finds and executes the given command, filling in response
    response = None
    user_command_str = ' '.join(command).lower()

    # see if user mentioned any of the key responses 
    if any(keyword in user_command_str for keyword in KEYWORDS):
        meme_title, meme_url = get_meme() 

    response = '> *' + meme_title + '* \n' +\
               '> ' + meme_url

    # Sends the response back to the channel
    slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response or default_response
            )


def get_meme():
    '''
        Uses PRAW to fetch a meme URL from reddit
    '''
    
    subreddit = reddit.subreddit(random.choice(SUBREDDITS))
    top_memes = list(subreddit.top(limit=25))

    meme_choice = random.choice(top_memes)
    content_type = get_content_type(meme_choice.url)
    content_size = len(requests.get(meme_choice.url).content)

    # verify that the returned url is an image to properly preview in slack
    while 'image' not in content_type or content_size > 1000000: 
        meme_choice = random.choice(top_memes)
        content_type = get_content_type(meme_choice.url)
        content_size = len(requests.get(meme_choice.url).content)

    print(subreddit)
    print(meme_choice.title)
    print(meme_choice.url)
    print(content_type)
    print(content_size)
    print()
    
    return meme_choice.title, meme_choice.url


def get_content_type(url):
    return requests.head(url).headers['Content-Type']


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
