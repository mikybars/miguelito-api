import decimal
from os import environ as env

import boto3
import botocore.exceptions
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb')
counters_table = dynamodb.Table(env['COUNTERS_TABLE'])


def new_link_id() -> int:
    return new_id('linkId')


def new_user_id() -> int:
    return new_id('userId')


def new_id(type: str) -> int:
    try:
        response = counters_table.update_item(
            Key={
                'name': type
            },
            UpdateExpression='set #value = #value + :inc',
            ExpressionAttributeNames={'#value': 'value'},
            ReturnValues='UPDATED_OLD',
            ConditionExpression=Attr('name').exists(),
            ExpressionAttributeValues={
                ':inc': decimal.Decimal(1)
            },
        )
        return response['Attributes']['value']
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return new_counter(type)
        raise


def new_counter(type: str) -> int:
    initial_value = 1
    counters_table.put_item(
        Item={
            'name': type,
            'value': initial_value
        }
    )
    return initial_value
