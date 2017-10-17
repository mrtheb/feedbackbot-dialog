'''
Feedbackbot - sns2sfdc
Subscribing To SNS For Salesforce Cases
Part of https://woobot.io/weve-got-somethin-for-ya/
'''
import os
import json
import logging

from simple_salesforce import Salesforce

LOGGER = logging.getLogger()
LOGGER.setLevel('INFO')

SFDC_USERNAME = os.environ.get('SFDC_USERNAME')
SFDC_PASSWORD = os.environ.get('SFDC_PASSWORD')
SFDC_SECURITY_TOKEN = os.environ.get('SFDC_SECURITY_TOKEN')

def lambda_handler(event, context): #pylint: disable=W0613
    ''' SNS to Salesforce Case '''

    sforce = Salesforce(
        username=SFDC_USERNAME,
        password=SFDC_PASSWORD,
        security_token=SFDC_SECURITY_TOKEN
    )

    for record in event['Records']:
        if 'Sns' not in record:
            LOGGER.warn('ERROR ABANDON RECORD:  Not an SNS event')
            continue

        subject = record['Sns']['Subject']

        if subject != 'feedback':
            LOGGER.warn('Non-feedback message in feedback SNS')
            continue

        feedback = json.loads(record['Sns']['Message'])

        sforce.Case.create({
            # These two fields are custom fields that need to be added to the Case object
            'Slack_User__c' : feedback['user_id'],
            'Slack_Team__c' : feedback['team_id'],
            'Subject' : feedback['text'][:250] + ('...' if len(feedback['text']) > 250 else ''),
            'Description' : feedback['text'] if len(feedback['text']) > 250 else '',
            'Origin' : 'Feedback',
            'Type': 'Feedback'
        })
