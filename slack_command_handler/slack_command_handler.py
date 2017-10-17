'''
Feedbackbot - slack_command_handler
Publishing to SNS from Slack Command
Part of https://woobot.io/weve-got-somethin-for-ya/
'''

import os
import sys
import traceback
import urlparse
import json
import logging
import requests
import boto3

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)

SNS = boto3.client('sns')

#  These two environment variables are required

# Slack Verification Token is the App Token that Slack provides when you create a Slack App.
# This uniquely identifier is included in payloads from Slack as proof of authentication

SLACK_VERIFICATION_TOKEN = os.environ.get('SLACK_VERIFICATION_TOKEN')

# Bot Access Token is the token unique to your bot's instance on your customer's slack team.
# This is obtained when your customers install your bot.

BOT_ACCESS_TOKEN = os.environ.get('BOT_ACCESS_TOKEN')


#
#  A few helper tools to decode x-www-form-urlencoded into dictionary format
#
class DecoderError(Exception):
    ''' Exception class for decoder '''
    pass

def flatten_dictionary_array(inp_x):
    ''' flatten a dict of arrays of 1 value to just key, value dict '''
    out_y = {}
    for key in inp_x:
        if len(inp_x[key]) == 1:
            out_y[key] = inp_x[key][0]
    return out_y

def decode_urlencoded(body):
    ''' decode x-www-form-urlencoded '''

    try:
        data = flatten_dictionary_array(urlparse.parse_qs(body, keep_blank_values=True))
    except ValueError:
        raise DecoderError('ERROR:  Can not parse body')
    except TypeError:
        raise DecoderError('ERROR:  Can not parse body')

    return data

#
#
#

def send_slack_dialog(feedback_text=None, bot_access_token=None, trigger_id=None, response_url=None):
    ''' send slack message to channel '''
    # Slack API requires both the bot_access_token and a trigger_id.
    # The trigger_id is provided when a user initiates a command or interactive message (button, or picklist)
    # Note that trigger_id is time-sensitive, as it expires within seconds of being issued.
    #  We encode the response_url in the callback_id so that we can send the user an ephemeral Thank you message

    dialog_msg = {
        "token": bot_access_token,
        "trigger_id": trigger_id,
        "dialog" : json.dumps({
            "title": "Feedback for Woobot",
            "callback_id": "Feedback__%s" % response_url,
            "submit_label": "Send",
            "elements": [{
                'type': "textarea",
                'label': 'Comments',
                'name': 'Comments',
                'hint': '(required)',
                'value': feedback_text
            }]
        })
    }

    #  We use the requests library, but other libraries would work as well
    response = requests.post(
        url='https://slack.com/api/dialog.open',
        params=dialog_msg,
        headers={'Content-type': 'application/json; charset=utf-8'}
        )

    if response.status_code > 299:  # bad request, or a system problem
        LOGGER.warning('Slack response code: %d, with text: %s\nAttempted to send: %s', response.status_code, response.text, dialog_msg)
    else:
        respobj = json.loads(response.text)
        # Slack usually responds with a 200 and embeds the actual response in JSON.
        #
        # An error message looks like:
        #    { 'ok': false, 'error': 'Error message' }
        #
        # A success looks like:
        #    { 'ok': true }
        #
        if 'ok' in respobj and not respobj['ok']:
            LOGGER.warning('Error sending to Slack endpoint: %s\nAttempted to send: %s', respobj['error'] if 'error' in respobj else '', dialog_msg)

    return None

#
#  Handler for lambda invocation from API Gateway
#

def lambda_handler(event, context):
    ''' Entry point for API Gateway '''

    if context:
        LOGGER.debug('Function ARN: %s', context.invoked_function_arn)
    else:
        LOGGER.warning('Lambda context is missing')

    slackmsg = None  # Success is None.  Otherwise used for error messaging.

    try:
        payload = decode_urlencoded(event['body'])

        if 'token' not in payload or (payload['token'] != SLACK_VERIFICATION_TOKEN):
            # This payload did NOT come from Slack.
            LOGGER.warning('Payload received from unverified source')
            raise ValueError('Verification token mismatch')

        if 'trigger_id' not in payload or not payload['trigger_id']:
            LOGGER.warning('trigger_id not found in payload')
            raise ValueError('Missing trigger_id')

        send_slack_dialog(
            feedback_text=payload['text'] if 'text' in payload else None,
            trigger_id=payload['trigger_id'],
            bot_access_token=BOT_ACCESS_TOKEN,
            response_url=payload['response_url'] if 'response_url' in payload else None
            )

    except Exception: # pylint: disable=W0703
        # Do not ever let them see you sweat. Hide internal error messages from the user.
        LOGGER.warning("ERROR: Unexpected error:\n".join(traceback.format_exception(*(sys.exc_info()))))
        LOGGER.warning("ERROR: Payload: %s", event['body'])
        slackmsg = ':cry: I did not understand that command.'
    finally:
        #  The user will receive a dialog open event through the dialog.open request call.
        #  This return result is for the slack command. Success is a 200 with an empty body.

        #  Note that this response object is specific to AWS API Gateway
        return { # pylint: disable=W0150
            'statusCode': 200,
            'headers': {'Content-type': 'application/json'},
            'body': slackmsg
        }
