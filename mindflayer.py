import slackclient
import os
import time
import re
import random
import pandas as pd
import markovify
import pickle
import datetime
import argparse
import csv

import config
SLACK_BOT_TOKEN = config.SLACK_BOT_TOKEN
SLACK_APP_TOKEN = config.SLACK_APP_TOKEN
TEST_ENV = config.TEST_ENV
PROD_ENV = config.PROD_ENV

def get_users():
    sc = slackclient.SlackClient(SLACK_BOT_TOKEN)
    r = sc.api_call("users.list")["members"]
    users = {x["id"]:re.sub(r'([^\s\w]|_)+', '', x["profile"]["real_name"]) for x in r if not x["deleted"]}
    return users

def get_channels():
    sc = slackclient.SlackClient(SLACK_BOT_TOKEN)
    raw_channel_list = sc.api_call("channels.list")
    channels = [(x["id"], x["name"]) for x in raw_channel_list["channels"] if not x["is_archived"]]
    return channels



def scrape_channels(channels, n=7):
    print(f"scraping last {n} days")
    sc = slackclient.SlackClient(SLACK_APP_TOKEN)
    oldest = datetime.datetime.now() - datetime.timedelta(days=int(n))
    oldest = datetime.datetime.timestamp(oldest)
    for channel in channels:
        try:
            # grab and make unique
            h = sc.api_call("channels.history", channel = channel[0], oldest = oldest)["messages"]
            if len(h) > 0:
                print(f"ingesting {channel[1]}")
                d = pd.DataFrame.from_dict(h)
                d = d[["user","text"]]
                with open(f"channels/{channel[1]}.csv", 'a') as f:
                    d.to_csv(f"channels/{channel[1]}.csv", mode='a', quoting=csv.QUOTE_NONNUMERIC, index=False, header=f.tell()==0)
        except:
            pass


def dedupe_channel_histories(channels):
    print("deduping channel histories")
    channels = os.listdir("channels")
    for channel in channels:
        try:
            c = pd.read_csv(f"channels/{channel}")
            c.drop_duplicates(inplace=True)
            c.to_csv(f"channels/{channel}", mode='w', quoting=csv.QUOTE_NONNUMERIC, index=False)
        except Exception as e:
            print(channel)
            print(e)

def truncate_user_histories(users):
    print("truncating user histories")
    for user in users.keys():
        try:
            with open(f"users/{users[user]}_{user}.txt", "w", encoding="utf-8") as f:
                f.truncate()
        except Exception as e:
            print(e)

def populate_user_histories(users):
    print("populating user histories")
    channels = os.listdir("channels")
    for channel in channels:
        try:
            c = pd.read_csv(f"channels/{channel}")
            for index, row in c.iterrows():
                    username = row["user"]
                    # print(username)
                    if str(username)[0] == "U" and username in users.keys():
                        with open(f"users/{users[username]}_{username}.txt", "a") as f:
                            f.write(str(row["text"]).encode('ascii', 'ignore').decode('ascii'))
                            f.write("\n")
        except Exception as e:
            print(channel, e)

def create_markov_models(users):
    print("building markov models")
    for user in users.keys():
        try:
            with open(f"users/{users[user]}_{user}.txt", encoding="utf-8") as f:
                text = f.read()
                name = user.split(".")[0]
                text_model = markovify.NewlineText(text)
                model_path = f"models/{name}.json"
                with open(model_path, "wb") as model_file:
                    pickle.dump(text_model, model_file)
                # print("success")

        except Exception as e:
            pass


# one time, this was used to combine old and new models
# old_models = os.listdir("old_models")
# for o in old_models:
#     print(o)
#     try:
#         with open(f"old_models/{o}", "rb") as old_model_file:
#                     old_model = pickle.load(old_model_file)
#                     with open(f"models/{o}", "rb") as new_model_file:
#                         new_model = pickle.load(new_model_file)
#                         combined_model = markovify.combine([old_model, new_model])
#                         with open(f"combined_models/{o}", "wb") as combined_model_file:
#                             pickle.dump(combined_model, combined_model_file)
#     except Exception as e:
#         print(e)

def make_sentences(users):
    print("generating candidate posts")
    models = [f"{user}.json" for user in users.keys()]
    # models = os.listdir("models")
    potench = {}
    for i in range(1000):
        model_name = random.choice(models)
        user_full = users[model_name.split(".")[0]]
        try:
            # print(model_name)
            with open(f"models/{model_name}", "rb") as model_file:
                model = pickle.load(model_file)
                sentance = model.make_sentence()
                if sentance:
                    potench[i] = [user_full, sentance]
        except Exception as e:
            print(e, user_full)
            pass
    return potench

def review_posts(candidate_posts):
    while True:
        for post in candidate_posts:
            print(candidate_posts[post][0],"\n", candidate_posts[post][1])
            reply = str(input("accept and post? (y/n): ")).lower().strip()
            if reply[0] == 'y':
                post_user = candidate_posts[post][0]
                post_text = candidate_posts[post][1]
                return post_user, post_text
            if reply[0] == 'n':
                pass

def post(env, post_user, post_text):
    sc = slackclient.SlackClient(SLACK_BOT_TOKEN)
    message_text = "*{}*\n{}".format(post_user, post_text)
    message_color = "#{}".format(hex(random.randint(0, 0xffffff))[2:])


    resp = sc.api_call(
        "chat.postMessage",
        channel=env,
        attachments=[{'text': message_text, 'color': message_color}],
        as_user = True
        )

    print(resp)


def main():
    parser = argparse.ArgumentParser(description='the upside down')
    subparser = parser.add_subparsers(dest="command")

    parser_train = subparser.add_parser("train")
    parser_train.add_argument('-n','--num', help='num days back to train', required=True, choices=['1','2','3','4','5','6','7'])

    parser_post = subparser.add_parser("post")
    parser_post.add_argument('-e','--env', help='test or prod', required=True, choices=['test', 'prod'])

    args = vars(parser.parse_args())

    users = get_users()
    channels = get_channels()


    if args["command"] == "train":
        num_days_back = args['num']
        scrape_channels(channels=channels ,n=num_days_back)
        dedupe_channel_histories(channels=channels)
        truncate_user_histories(users=users)
        populate_user_histories(users=users)
        create_markov_models(users=users)

    if args["command"] == "post":
        env = args['env']
        if env == 'test':
            slack_chan = TEST_ENV
        if env == 'prod':
            slack_chan = PROD_ENV
        candidates = make_sentences(users=users)
        chosen_post_user, chosen_post_text = review_posts(candidate_posts=candidates)
        post(env=slack_chan, post_user=chosen_post_user, post_text=chosen_post_text)


if __name__ == '__main__':
    main()
