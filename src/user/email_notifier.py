from os import environ as env

import boto3

ses_client = boto3.client('ses')

MAINTAINER_EMAIL = env['MAINTAINER_EMAIL']
DOMAIN_NAME = env['BUCKET_NAME']


def notify_request_to_join(user_name, user_email):
    ses_client.send_email(
        Source=f'{DOMAIN_NAME}.to <{MAINTAINER_EMAIL}>',
        Destination={
            'ToAddresses': [
                MAINTAINER_EMAIL,
            ],
        },
        Message={
            'Body': {
                'Html': {
                    'Data': '',
                },
                'Text': {
                    'Data': '',
                },
            },
            'Subject': {
                'Charset': 'UTF-8',
                'Data': f'🙏 New request to join from {user_name} <{user_email}>',
            },
        },
    )


def notify_account_activated(user_email):
    ses_client.send_email(
        Source=f'{DOMAIN_NAME} <{MAINTAINER_EMAIL}>',
        Destination={
            'ToAddresses': [
                user_email
            ],
        },
        Message={
            'Body': {
                'Html': {
                    'Data': '',
                },
                'Text': {
                    'Data': '',
                },
            },
            'Subject': {
                'Charset': 'UTF-8',
                'Data': 'Your account is now activated 💃',
            },
        },
    )
