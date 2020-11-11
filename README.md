# mindflayer
![hasbadges](https://z2x6abi6e2.execute-api.us-east-1.amazonaws.com/v1/hasbadges?user=hinnefe2&repo=gitrisky)

The Mind Flayer, also known as the Shadow Monster, is a malevolent entity that rules the parallel dimension known as the Upside Down.

This code trains markov models on your organizations public slack messages and provides a simple CLI for posting to a channel.

<img src="https://github.com/WillRaphaelson/mindflayer/blob/master/screenshot.png">

## Installation
```
git clone git@github.com:WillRaphaelson/mindflayer.git
cd mindflayer/
pip install -r requirements.txt
```

## Configuration

### Slack-side

Create an app in your workspace at https://api.slack.com/apps, and add in the following app and user scopes.

**Bot Token Scopes**

| Scope        | Description   |
| ------------- |-------------|
| channels:join      | Join public channels in the workspace|
| channels:manage      | Manage public channels that Mindflayer has been added to and create new ones|
| channels:read      | View basic information about public channels in the workspace|
| chat:write | Send messages as @mindflayer|
| chat:write.public | Send messages to channels @mindflayer isn't a member of|
| groups:history | View messages and other content in private channels that Mindflayer has been added to|
| groups:write | Manage private channels that Mindflayer has been added to and create new ones|
| im:write | Start direct messages with people |
| mpim:write | Start group direct messages with people |
| users:read | View people in the workspace      |

Install the application, and securely store the Bot And User OAuth Access Token for use in the config file detailed below.

### Local

**config.py**

A `config.py` file in the top level directory will provide key configuration variables. The slack bot and app token are take from the app's permissions page in Slack.

```
SLACK_BOT_TOKEN = "xxxx-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx"
TEST_ENV = "GS6CFBN5N"
PROD_ENV = "CBHJ17SVC"
```

**subdirectories**

Subdirectory structure and contents are important:

```
  .
  ├── ...
  ├── channels               # csv files of channel histories
  │   ├── data.csv           
  │   └── ...
  ├── users                  # txt files of user posts
  │   ├── Will_Arr_U001.txt         
  │   └── ...
  ├── models                 # json files of pickled markov models
  │   ├── U001.json         
  │   └── ...∑
  └── ...
```

## Usage
The `train` command will scrape, parse, and train new models based on data from the last `num` days.

```
python mindflayer.py train --num 1
```

The `post` command will surface randomly generated sentences, and prompt for posting in either the `test` or `prod` channels.

```
python mindflayer.py post --env test
Review Posts:

Will Arr
Thank you for the Software Engineering Intern interviews
accept and post? (y/n):
```

To generate and post sentences for a specific user, provide the optional `--user` argument followed by a users slack ID

```
python mindflayer.py post --env test --user UBGGK785R
```

To generate and post sentences from the mindflayer itself, user the `post-arbitrary` argument followed by the `--env` and `--mssg` arguments

| WARNING: only post messages from the mindflayer when it is hella funny |
| --- |

```
python mindflayer.py post-arbitrary
--env test
--mssg "okay b4 the holiday party do any1 wanna admit they got a crush on me"
```
