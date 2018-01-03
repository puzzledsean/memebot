import os
import time
import random 
import requests
import praw
import redis
import json

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

# instantiate redis
redis_db = redis.from_url(os.environ.get("REDIS_URL")) 

# redis for local
#  redis_db = redis.Redis(host="localhost", port=6379, db=0)

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


def cache_memes():
    '''
        Uses PRAW to fetch and cache all memes from the SUBREDDITS list in the past 24 hours

        Returns:
            - True upon successful cache of memes into Redis, False otherwise
    '''

    master_list = []

    # cache content from each subreddit
    for subreddit in SUBREDDITS:
        print('Added r/{} to master list...'.format(subreddit))
        curr_subreddit = reddit.subreddit(subreddit)
        top_memes = list(curr_subreddit.top(limit=50))
        random.shuffle(top_memes)
        
        # cache each meme's title and url
        for meme in top_memes:
            try:
                content_type = get_content_type(meme.url)
            except:
                print('An error occurred getting content type for url: {}'.format(meme.url))
                continue

            content_size = len(requests.get(meme.url).content)
            if 'image' not in content_type or content_size > 1000000:
                continue

            # append meme info to master list
            meme_content = [subreddit, meme.title, meme.url, meme.id]
            master_list.append(meme_content)

    # cache master list 
    master_list = json.dumps(master_list)

    if redis_db.set('cache', master_list):
        return True
    return False


def get_meme():
    '''
        Fetches a random meme from the redis cache

        Returns:
            - meme title
            - meme image URL
    '''
    
    # fetch cached memes
    cached_meme_list = json.loads(redis_db.get('cache'))

    # if all memes have been seen/removed from cache, re-index the subreddits 
    if len(cached_meme_list) == 0:
        cache_memes()
        cached_meme_list = json.loads(redis_db.get('cache'))

    # choose a random meme from cache
    meme_choice = random.choice(cached_meme_list)
    meme_title = meme_choice[1]
    meme_url = meme_choice[2]
    meme_id = meme_choice[3]
    print('id of meme posted:', meme_id)
    
    # remove meme from cache to avoid duplicates
    cached_meme_list.remove(meme_choice)
    cached_meme_list = json.dumps(cached_meme_list)
    redis_db.set('cache', cached_meme_list)
    
    return meme_title, meme_url


def get_content_type(url):
    '''
        Get content type of meme url. Used to verify that the URL is an image
    '''
    return requests.head(url).headers['Content-Type']


def listen():
    '''
        Infinitely loops, listening to Slack for events every RTM_READ_DELAY interval.
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


def run():
    '''
        Run the app.
    '''

    # check if cache is empty
    cache = redis_db.get('cache')
    if cache is None: 
        print('Caching new memes...')
        if not cache_memes():
            print('Error indexing subreddits.')
            return 
        print('Cached all new memes. Launching memebot...')
    else:
        print('Memes have previously been cached. Launching memebot...')

    listen()


if __name__ == "__main__":
    run()
