'''
Feedbackbot - slack2sns
Publishing to SNS from Slack Command
Part of https://woobot.io/weve-got-somethin-for-ya/
'''

import os
import logging
import json
import urlparse
from urllib2 import Request, urlopen, URLError, HTTPError
import boto3

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)

SNS = boto3.client('sns')

SLACK_VERIFICATION_TOKEN = os.environ.get('SLACK_VERIFICATION_TOKEN')
SNS_FEEDBACK_ARN = os.environ.get('SNS_FEEDBACK_ARN')

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

    LOGGER.debug('Function ARN: %s', context.invoked_function_arn)

    msgtext = None
    try:
        payload = decode_urlencoded(event['body'])

        if 'token' not in payload or (payload['token'] != SLACK_VERIFICATION_TOKEN):
            # This payload did NOT come from Slack.
            LOGGER.warning('Payload received from unverified source')
            return

        if 'callback_id' not in payload or payload['callback_id'] is None:
            LOGGER.warning('No callback_id')
            return

        if payload['callback_id'][':10'] != 'Feedback__':
            LOGGER.warning('Callback does not begin with Feedback__')
            return

        # Pull the response_url from the callback_id
        response_url = payload['callback_id'][10:]

        if 'dialog_submission' not in payload or payload['dialog_submission'] is None:
            msgtext = ':cry: No comments were included! You gotta give me something to work with here!'
        else:
            message = {
                'user_id': payload['user']['id'],
                'user_name': payload['user']['name'],
                'team_id': payload['team']['id'],
                'team_domain': payload['team']['domain'],
                'text': payload['dialog_submission']['text']
            }
            SNS.publish(
                TopicArn=SNS_FEEDBACK_ARN,
                Message=json.dumps(message),
                Subject='feedback'
            )
            msgtext = ':ok_hand: Thanks for sharing your message. We\'ll hit you back soon!'


        #  Response to the user with an ephemeral message
        req = Request(response_url, json.dumps({
            'text' : msgtext,
            'mrkdwn': True,
        }))
        try:
            response = urlopen(req)
            response.read()
            LOGGER.info('Message posted')
        except HTTPError as exc:
            LOGGER.error('Request failed: %d %s', exc.code, exc.reason)
        except URLError as exc:
            LOGGER.error('Server connection failed: %s', exc.reason)


    except Exception: # pylint: disable=W0703
        # Do not ever let them see you sweat
        msgtext = ':cry: No comments were included! You gotta give me something to work with here!'


    #  This response is directed to the Dialog in Slack. We should return 200 OK with empty body
    return {
        'statusCode': 200,
        'headers': {'Content-type': 'application/json'},
        'body': None
    }
