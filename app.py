import os
import sys
import json
from datetime import datetime

import requests
from flask import Flask, request

from messages import *

app = Flask(__name__)

state    = {}
language = {}

@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        #if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
        if not request.args.get("hub.verify_token") == "flamboyant":
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text
                    
                    if sender_id not in state:
                    
                        # First message
                        send_message(sender_id, "Hi, {}".format(sender_id) )
                        send_message(sender_id, msg_start )
                        state[sender_id] = 1
                    else:
                        # Already started a conversation
                        if state[sender_id] == 1:
                            # Get the language
                            print(message_text)
                            
                            if message_text == "1":
                                language[sender_id] = "english"
                            elif message_text == "2":
                                language[sender_id] = "spanish"
                            elif message_text == "3":
                                language[sender_id] = "portuguese"
                            else:
                                language[sender_id] = "english"
                        
                            send_message(sender_id, msg_likes[language[sender_id]] )
                            state[sender_id] = 2
                        
                        elif state[sender_id] == 2:
                            send_message(sender_id, msg_spend[language[sender_id]] )
                            state[sender_id] = 3
                        
                        else:
                            send_message(sender_id, msg_great_day[language[sender_id]] )

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200


def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = { "access_token": os.environ["PAGE_ACCESS_TOKEN"] }
    headers = {   "Content-Type": "application/json" }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(msg, *args, **kwargs):  # simple wrapper for logging to stdout on heroku
    try:
        if type(msg) is dict:
            msg = json.dumps(msg)
        else:
            msg = msg.format(*args, **kwargs)
        print("{}: {}".format(datetime.now(), msg))
    except UnicodeEncodeError:
        pass  # squash logging errors in case of non-ascii text
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
