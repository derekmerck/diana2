import os
import slack
import sys


@slack.RTMClient.run_on(event='message')
def process_slack_message(**payload):
    print("Received Slack Message")
    data = payload['data']
    web_client = payload['web_client']
    channel_id = data['channel']
    thread_ts = data['ts']
    if "user" not in list(data.keys()):
        return
    user = data['user']

    if '//last' in data['text']:
        web_client.chat_postMessage(
            channel=channel_id,
            text=f"Recent bone age study requested - <@{user}>",
            thread_ts=thread_ts
        )
    elif '//flush' in data['text']:
        web_client.chat_postMessage(
            channel=channel_id,
            text=f"Flush requested - <@{user}>",
            thread_ts=thread_ts
        )
    elif '//process' in data['text']:
        an = data['text'].split(" ")[1]
        with open("/diana_direct/{}/{}_scores.txt".format(ML, ML), "r") as f:
            lines = f.readlines()
        with open("/diana_direct/{}/{}_scores.txt".format(ML, ML), "w") as f:
            for line in lines:
                if an not in line:
                    f.write(line)
        with open("/diana_direct/{}/{}_slack_an.txt".format(ML, ML), "w+") as f:
            f.write(an)
        web_client.chat_postMessage(
            channel=channel_id,
            text=f"Processing of accession number {an} requested - <@{user}>",
            thread_ts=thread_ts
        )


if __name__ == "__main__":
    global ML
    ML = sys.argv[1]
    print(ML)
    rtm_client = slack.RTMClient(token=os.environ["SLACK_BOT_TOKEN"])
    rtm_client.start()
