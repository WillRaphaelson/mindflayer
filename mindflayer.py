# Maybe just have a validation function up top to confirm required scopes? <- do that
# possibly distribute for installation?
# different workspaces?

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
import sys

import config
SLACK_BOT_TOKEN = config.SLACK_BOT_TOKEN
SLACK_USER_TOKEN = config.SLACK_USER_TOKEN
TEST_ENV = config.TEST_ENV
PROD_ENV = config.PROD_ENV

def get_users(bot_token):
    # print("Getting active user list")
    sc = slackclient.SlackClient(bot_token)
    try:
        r = sc.api_call("users.list")
        r = sc.api_call("users.list")["members"]
    except KeyError:
        r = sc.api_call("users.list")
        scope = r["needed"]
        print(f"Missing scope: {scope}")
        return
    users = {x["id"]:re.sub(r'([^\s\w]|_)+', '', x["profile"]["real_name"]) for x in r if not x["deleted"]}
    return users


def get_channels(bot_token):
    print("Getting public channel list")
    sc = slackclient.SlackClient(bot_token)
    raw_channel_list = sc.api_call("channels.list")
    # print(raw_channel_list)
    channels = [(x["id"], x["name"]) for x in raw_channel_list["channels"] if not x["is_archived"]]
    # print(f"channels list: {channels}")
    return channels

def scrape_channels(app_token, channels, n=7):
    print(f"Scraping last {n} days")
    sc = slackclient.SlackClient(app_token)
    oldest = datetime.datetime.now() - datetime.timedelta(days=int(n))
    oldest = datetime.datetime.timestamp(oldest)
    no_messages_list = []
    for channel in channels:
        try:
            # print(f"Ingesting {channel[1]}")
            # grab and make unique
            h = sc.api_call("channels.history", channel = channel[0], oldest = oldest)["messages"]
            # print(h)
            d = pd.DataFrame.from_dict(h)
            d = d[["user","text"]]
            with open(f"channels/{channel[1]}.csv", 'a') as f:
                d.to_csv(f"channels/{channel[1]}.csv", mode='a', quoting=csv.QUOTE_NONNUMERIC, index=False, header=f.tell()==0)
            num_messages = len(h)
            print(f"{num_messages} ingested for {channel[1]}")
        except KeyError as e:
            no_messages_list.append(channel[1])
    print("No messages found for:")
    print(no_messages_list)
    print("\n")




def dedupe_channel_histories(channels):
    print("Deduping channel corpora")
    channels = os.listdir("channels")
    channels = [x for x in channels if x[0] != "."]
    for channel in channels:
        try:
            c = pd.read_csv(f"channels/{channel}")
            c.drop_duplicates(inplace=True)
            c.to_csv(f"channels/{channel}", mode='w', quoting=csv.QUOTE_NONNUMERIC, index=False)
        except Exception as e:
            print(channel)
            print(e)


def truncate_user_histories(users):
    print("Truncating user corpora")
    for user in users.keys():
        try:
            with open(f"users/{users[user]}_{user}.txt", "w", encoding="utf-8") as f:
                f.truncate()
        except Exception as e:
            print(e)


def populate_user_histories(users):
    print("Populating user corpora")
    channels = os.listdir("channels")
    channels = [x for x in channels if x[0] != "."]
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
    print("Building markov models")
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

def make_sentences(users, user=None):
    print("Generating candidate posts")
    if not user:
        models = [f"{user}.json" for user in users.keys()]
    else:
        models = [f"{user}.json"]
    # models = os.listdir("models")
    potench = {}
    no_models_list = []
    for i in range(1000):
        model_name = random.choice(models)
        user_full = users[model_name.split(".")[0]]
        tag_name = re.search(r"(.*)\.json", model_name).group(1)
        try:
            # print(model_name)
            with open(f"models/{model_name}", "rb") as model_file:
                model = pickle.load(model_file)
                sentance = model.make_sentence()
                if sentance:
                    potench[i] = [user_full, sentance, tag_name]
        except Exception as e:
            no_models_list.append(user_full)
            pass
    print("No models found for:")
    print(list(set(no_models_list)))
    print("\n")
    return potench


def review_posts(candidate_posts):
    if len(candidate_posts) > 0:
        print("Review Posts:")
        while True:
            for post in candidate_posts:
                print(candidate_posts[post][0])
                print(candidate_posts[post][1])
                reply = str(input("accept and post? (y/n): ")).lower().strip()
                try:
                    if reply[0] == 'y':
                        post_user = candidate_posts[post][0]
                        post_text = candidate_posts[post][1]
                        tag_name = candidate_posts[post][2]
                        print("\n")
                        return post_user, post_text, tag_name
                    else:
                        print("\n")
                except IndexError as e:
                    print("\n")
                    pass
    else:
        print("Corpus too small to generate sentences, try another user.")
        sys.exit()


def post(bot_token ,env, tag_name, post_text):
    print("Posting to channel")
    print("Response:")
    sc = slackclient.SlackClient(bot_token)
    message_text = "<@{}>\n{}".format(tag_name, post_text)
    message_color = "#{}".format(hex(random.randint(0, 0xffffff))[2:])

    resp = sc.api_call(
        "chat.postMessage",
        link_names=1,
        channel=env,
        attachments=[{'text': message_text, 'color': message_color}],
        as_user = True
        )

    print(resp)

    resp = sc.api_call(
        "conversations.invite",
        link_names=1,
        channel=env,
        users=[tag_name],
        as_user = True
        )

    print(resp)

def post_arbitrary(bot_token ,env, post_text):
    print("Posting to channel")
    print("Response:")
    sc = slackclient.SlackClient(bot_token)
    message_text = post_text
    message_color = "#{}".format(hex(random.randint(0, 0xffffff))[2:])


    resp = sc.api_call(
        "chat.postMessage",
        link_names=1,
        channel=env,
        attachments=[{'text': message_text, 'color': message_color}],
        as_user = True
        )

    print(resp)


def delete_mssg(bot_token ,env, ts):
    sc = slackclient.SlackClient(bot_token)
    print(f"Deleting message with timestamp: {str(ts)}")
    print("Response:")
    resp = sc.api_call(
        "chat.delete",
        channel=env,
        ts=str(ts)
        )
    print(resp)


# @Gooey
def main():
    users = get_users(bot_token=SLACK_BOT_TOKEN)
    user_id_help = "\n".join([f"{x}: {v}" for v,x in users.items()])
    user_id_help = "Takes a user id from the following list: \n" + user_id_help

    parser = argparse.ArgumentParser(description='the upside down')
    subparser = parser.add_subparsers(dest="command")

    parser_train = subparser.add_parser("train")
    parser_train.add_argument('-n','--num', help='num days back to train', required=True, choices=['1','2','3','4','5','6','7','200'])

    parser_post = subparser.add_parser("post")
    parser_post.add_argument('-e','--env', help='test or prod', required=True, choices=['test', 'prod'])
    parser_post.add_argument('-u','--user', help=user_id_help, required=False, default=None)

    parser_post = subparser.add_parser("post-arbitrary")
    parser_post.add_argument('-e','--env', help='test or prod', required=True, choices=['test', 'prod'])
    # parser_post.add_argument('-u','--user', help=user_id_help, required=False, default=None)
    parser_post.add_argument('-m','--mssg', help='your mssg', required=True)

    parser_post = subparser.add_parser("delete-post")
    parser_post.add_argument('-e','--env', help='test or prod', required=True, choices=['test', 'prod'])
    # parser_post.add_argument('-u','--user', help=user_id_help, required=False, default=None)
    parser_post.add_argument('-t','--ts', help='timestamp of mssg to be deleted', required=True)

    args = vars(parser.parse_args())

    if args["command"] == "train":
        num_days_back = args['num']
        channels = get_channels(bot_token=SLACK_USER_TOKEN)
        scrape_channels(app_token=SLACK_BOT_TOKEN, channels=channels, n=num_days_back)
        dedupe_channel_histories(channels=channels)
        truncate_user_histories(users=users)
        populate_user_histories(users=users)
        create_markov_models(users=users)

    if args["command"] == "post":
        env = args['env']
        user = args['user']
        if env == 'test':
            slack_chan = TEST_ENV
        if env == 'prod':
            slack_chan = PROD_ENV
        candidates = make_sentences(users=users, user=user)
        chosen_post_user, chosen_post_text, tag_name = review_posts(candidate_posts=candidates)
        post(bot_token=SLACK_USER_TOKEN ,env=slack_chan, tag_name=tag_name, post_text=chosen_post_text)

    if args["command"] == "post-arbitrary":
        env = args['env']
        post_text = args["mssg"]
        if env == 'test':
            slack_chan = TEST_ENV
        if env == 'prod':
            slack_chan = PROD_ENV
        post_arbitrary(bot_token=SLACK_USER_TOKEN ,env=slack_chan, post_text=post_text)

    if args["command"] == "delete-post":
        ts = str(args['ts'])
        if env == 'test':
            slack_chan = TEST_ENV
        if env == 'prod':
            slack_chan = PROD_ENV
        delete_mssg(bot_token=SLACK_BOT_TOKEN ,env=slack_chan, ts=ts)


if __name__ == '__main__':
    main()
