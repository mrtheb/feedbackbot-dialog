# feedbackbot-dialog

Update to feedbackbot-slack2sns.  This update introduces the Slack Dialog feature.

This app is divided into 4 python handlers. Each can be run as a separate lambda function.

## Lambda Functions

#### 1. slack_command_handler
Receives slack commands and sends dialog to user.

#### 2. slack_dialog_handler
Receives slack dialog submission event and sends message to SNS.

#### 3. sns2slack
Receives SNS message and sends Slack notification

#### 4. sns2salesforce
Receives SNS message and creates a Case record in Salesforce

## Lambda Environment Variables

#### 1. SLACK_VERIFICATION_TOKEN
This token is provided by Slack and is unique to your Slack app. Use this to validate that the payloads received by your API Gateway originated from your Slack app.

#### 2. SNS_FEEDBACK_ARN
The unique ARN identifier for the SNS topic. This is created either by AWS command line or AWS Console. The SNS topic is the communication broker between the lambda functions.
