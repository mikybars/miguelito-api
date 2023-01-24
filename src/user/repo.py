from os import environ as env
from typing import Dict, List, Union

import boto3
import botocore.exceptions
from boto3.dynamodb.conditions import Attr, Key

from src.common.counters import new_user_id
from src.user.user import AdminUser, TestUser, UnknownUser, User, UserUpdate

dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table(env['USERS_TABLE'])

MAINTAINER_EMAIL = env['MAINTAINER_EMAIL']
DOMAIN_NAME = env['BUCKET_NAME']


def create(new_user: User) -> User:
    new_user.id = new_user_id()
    try:
        dynamodb.meta.client.transact_write_items(
            TransactItems=[
                {
                    'Put': {
                        'TableName': env['USERS_TABLE'],
                        'Item': new_user.asdict(),
                        'ConditionExpression': 'attribute_not_exists(#i)',
                        'ExpressionAttributeNames': {'#i': 'id'},
                    },
                },
                {
                    'Put': {
                        'TableName': env['UNIQUES_TABLE'],
                        'Item': {
                            'type': 'email',
                            'value': new_user.email,
                        },
                        'ConditionExpression': 'attribute_not_exists(#t)',
                        'ExpressionAttributeNames': {'#t': 'type'},
                    },
                },
            ]
        )
        return new_user
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != 'TransactionCanceledException':
            raise
        if e.response['CancellationReasons'][0]['Code'] != 'None':
            raise  # if the id is taken then we had a concurrency issue
        raise UserAlreadyExistsError


def find_by_email(email: str) -> User:
    if email == MAINTAINER_EMAIL:
        return AdminUser()
    if email.endswith(f'@{DOMAIN_NAME}'):
        return TestUser()
    response = users_table.query(
        IndexName='Email-index',
        KeyConditionExpression=Key('email').eq(email),
    )
    return as_user(response) if response['Count'] > 0 else UnknownUser()


def find_all() -> List[User]:
    scan = users_table.scan()
    users = [as_user(item) for item in scan['Items']]
    return sorted(users, key=lambda u: u.id)


def update(user_id: int, user_update: UserUpdate) -> User:
    try:
        response = users_table.update_item(
            Key={
                'id': user_id,
            },
            ConditionExpression=Attr('id').exists(),
            **update_item_params(user_update.asdict()),
            ReturnValues='ALL_NEW'
        )
        return as_user(response)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise UserNotFoundError
        raise


def delete(user_id: int) -> None:
    user = find_by_id(user_id)  # we also need to delete her email unique
    if user is None:
        return
    dynamodb.meta.client.transact_write_items(
        TransactItems=[
            {
                'Delete': {
                    'TableName': env['USERS_TABLE'],
                    'Key': {'id': user_id},
                },
            },
            {
                'Delete': {
                    'TableName': env['UNIQUES_TABLE'],
                    'Key': {
                        'type': 'email',
                        'value': user.email,
                    },
                },
            },
        ]
    )


def find_by_id(user_id: int) -> Union[User, None]:
    response = users_table.get_item(
        Key={'id': user_id}
    )
    return as_user(response) if 'Item' in response else None


def update_item_params(d):
    return {
        'UpdateExpression': f'SET {", ".join(f"#p{i} = :v{i}" for i in range(len(d)))}',
        'ExpressionAttributeNames': {f'#p{idx}': name for (idx, name) in enumerate(d.keys())},
        'ExpressionAttributeValues': {f':v{idx}': value for (idx, value) in enumerate(d.values())},
    }


def as_user(response: Dict) -> User:
    if 'Item' in response:
        user_data = response['Item']
    elif 'Items' in response:
        user_data = response['Items'][0]
    elif 'Attributes' in response:
        user_data = response['Attributes']
    else:
        user_data = response
    return User(**user_data)


class UserNotFoundError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass
