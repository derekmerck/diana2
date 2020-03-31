import yaml
from trial_dispatcher import TrialDispatcher as Dispatcher

EMAIL_DRYRUN = True

subscriptions = """\
---
trial_abc: "ABC National Trial"
trial_def: "DEF International Trial"
site_xxx:  "XXX Regional Site"
site_yyy:  "YYY City Site"

---

- name:     "John Doe"
  affiliation: "site_xxx"
  email:    "john@xxx.com"
  channels: ["trial_abc"]

- name:     "Alice Cooper"
  affiliation: "site_xxx"
  email:    "alice@xxx.com"
  channels: ["site_xxx"]

- name:     "Emily Brown"
  affiliation: "site_yyy"
  email:    "em@yyy.com"
  channels: ["trial_abc-site_yyy"]

- name:     "Jane Smith"
  affiliation: "site_yyy"
  email:    "jane@yyy.com"
  channels: ["trial_def"]
...
"""

def test_dispatch(dispatcher):

    item = {"meta": {
        "signature": {
            "trial": "trial_abc",
            "site":  "site_yyy"
        },
    },
        "data": "AaaBbbCcc yyy etc etc"
    }
    sent = dispatcher.put(item, dryrun=EMAIL_DRYRUN)

    print(sent)

    assert( "John Doe" in [ item['recipient']["name"] for item in sent] )
    assert( "Emily Brown" in [ item['recipient']["name"] for item in sent] )

    item = {"meta": {
        "signature": {
            "trial": "trial_abc",
            "site":  "site_xxx"
        },
    },
        "data": "AaaBbbCcc xxx etc etc"
    }
    sent = dispatcher.put(item, dryrun=EMAIL_DRYRUN)

    assert( "Alice Cooper" in [ item['recipient']["name"] for item in sent] )
    assert( "John Doe" in [ item['recipient']["name"] for item in sent] )


    item = {"meta": {
        "signature": {
            "trial": "trial_def",
            "site":  "site_xxx"
        },
    },
        "data": "DddEeeFff xxx etc etc"
    }
    sent = dispatcher.put(item, dryrun=EMAIL_DRYRUN)

    assert( "Alice Cooper" in [ item['recipient']["name"] for item in sent] )
    assert( "Jane Smith" in [ item['recipient']["name"] for item in sent] )


if __name__ == "__main__":

    channel_tags, subscribers = yaml.safe_load_all(subscriptions)
    dispatcher = Dispatcher(channel_tags=channel_tags)
    dispatcher.add_subscribers(subscribers)

    test_dispatch(dispatcher)
