source .env

# slack client
export SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN
export SLACK_BOT_ID=$SLACK_BOT_ID
export ACCESS_TOKEN=$ACCESS_TOKEN

# praw client
export REDDIT_CLIENT_ID=$REDDIT_CLIENT_ID
export REDDIT_CLIENT_SECRET=$REDDIT_CLIENT_SECRET
export REDDIT_USER=$REDDIT_USER
export REDDIT_PW=$REDDIT_PW

# heroku redis
export REDIS_HOST=$REDIS_HOST
export REDIS_PORT=$REDIS_PORT


echo "initialized environment variables"
