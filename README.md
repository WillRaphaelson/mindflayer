# mindflayer
![hasbadges](https://z2x6abi6e2.execute-api.us-east-1.amazonaws.com/v1/hasbadges?user=hinnefe2&repo=gitrisky)

The Mind Flayer, also known as the Shadow Monster, is a malevolent entity that rules the parallel dimension known as the Upside Down.

## Installation
```
git clone git@github.com:WillRaphaelson/mindflayer.git
cd mindflayer/
pip install -r requirements.txt
```

## Configuration
The following files cannot be checked in to git for privacy and security reasons. Contact the maintainers for access.

### config.py
A `config.py` file in the top level directory will provide key environmental variables:

```
SLACK_BOT_TOKEN = "xxxx-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx"
SLACK_APP_TOKEN = "xxxx-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TEST_ENV = "CMGRE0222"
PROD_ENV = "CBHJ17SVC"
```

### subdirectories
Subdirectory structure and contents are important:

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
  │   └── ...
  └── ...


## Usage
The `train` command will scrape, parse, and train new models based on data from the last `n` days.

```
python mindflayer.py train --num 1
```

The `post` command will surface randomly generated sentences, and prompt for posting in either the `test` or `prod` channels.

```
python mindflayer.py post --env test
```
