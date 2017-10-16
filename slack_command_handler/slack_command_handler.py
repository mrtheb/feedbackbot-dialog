'''
Feedbackbot - slack_command_handler
Publishing to SNS from Slack Command
Part of https://woobot.io/weve-got-somethin-for-ya/
'''

import os
import sys
import traceback
import urlparse
import logging
import boto3

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)

SNS = boto3.client('sns')

SLACK_VERIFICATION_TOKEN = os.environ.get('SLACK_VERIFICATION_TOKEN')

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

    except Exception: # pylint: disable=W0703
        # Do not ever let them see you sweat. Hide internal error messages from the user.
        LOGGER.warning("ERROR: Unexpected error:\n".join(traceback.format_exception(*(sys.exc_info()))))
        LOGGER.warning("ERROR: Payload: %s", event['body'])
        slackmsg = ':cry: I did not understand that command.'
    finally:
        #  The user will receive a dialog open event through the dialog.open request call.
        #  This return result is for the slack command. Success is a 200 with an empty body.
        return { # pylint: disable=W0150
            'statusCode': 200,
            'headers': {'Content-type': 'application/json'},
            'body': slackmsg
        }
