from os import environ as env
from typing import Dict, List, Union

import boto3
import botocore.exceptions
from boto3.dynamodb.conditions import Attr, Key

from src.common.counters import new_link_id
from src.link.link import Link, LinkUpdate

dynamodb = boto3.resource('dynamodb')
bucket = boto3.resource('s3').Bucket(env['BUCKET_NAME'])
links_table = boto3.resource('dynamodb').Table(env['LINKS_TABLE'])
uniques_table = dynamodb.Table(env['UNIQUES_TABLE'])


def create(new_link: Link) -> Link:
    new_link.id = new_link_id()
    insert_record(new_link)
    set_redirect(new_link)
    return new_link


def find_by_user(user: str) -> List[Link]:
    result = links_table.query(
        IndexName='User-index',
        KeyConditionExpression=Key('user').eq(user),
    )
    return [as_link(item) for item in result['Items']]


def find_all() -> List[Link]:
    scan = links_table.scan()
    return [as_link(item) for item in scan['Items']]


def update_if_owned_by_user(backhalf: str, link_update: LinkUpdate, user: str) -> Link:
    if link_update.backhalf is None:
        updated_link = update_record(backhalf, link_update, user)
        set_redirect(updated_link)
    else:  # preserve the unique constraint
        updated_link = update_record_with_new_backhalf(backhalf, link_update, user)
        set_redirect(updated_link)
        unset_redirect(backhalf)
    return updated_link


def update(backhalf: str, link_update: LinkUpdate) -> Link:
    if link_update.backhalf is None:
        updated_link = update_record(backhalf, link_update)
        set_redirect(updated_link)
    else:  # preserve the unique constraint
        updated_link = update_record_with_new_backhalf(backhalf, link_update)
        set_redirect(updated_link)
        unset_redirect(backhalf)
    return updated_link


def delete(backhalf: str):
    delete_record(backhalf)
    unset_redirect(backhalf)


def delete_if_owned_by_user(backhalf: str, user: str):
    delete_record(backhalf, user)
    unset_redirect(backhalf)


def delete_all():
    delete_all_records()
    unset_all_redirects()


def insert_record(new_link: Link):
    try:
        dynamodb.meta.client.transact_write_items(
            TransactItems=[
                {
                    'Put': {
                        'TableName': env['LINKS_TABLE'],
                        'Item': new_link.asdict(),
                        'ConditionExpression': 'attribute_not_exists(#i)',
                        'ExpressionAttributeNames': {'#i': 'id'},
                    },
                },
                {
                    'Put': {
                        'TableName': env['UNIQUES_TABLE'],
                        'Item': {
                            'type': 'backhalf',
                            'value': new_link.backhalf,
                            'link_id': new_link.id,
                        },
                        'ConditionExpression': 'attribute_not_exists(#t)',
                        'ExpressionAttributeNames': {'#t': 'type'},
                    },
                },
            ]
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != 'TransactionCanceledException':
            raise
        if e.response['CancellationReasons'][0]['Code'] != 'None':
            raise  # if the id is taken then we had a concurrency issue
        raise LinkAlreadyExistsError


def update_record(backhalf: str, link_update: LinkUpdate, user: str = None) -> Link:
    try:
        link_id = get_link_id(backhalf)
        response = links_table.update_item(
            Key={
                'id': link_id
            },
            **update_link_args(link_update, user),
            ReturnValues='ALL_NEW'
        )
        return as_link(response)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
            raise
        raise NotOwnedByUserError


def update_record_with_new_backhalf(old_backhalf: str, link_update: LinkUpdate, user: str = None) -> Link:
    try:
        link_id = get_link_id(old_backhalf)
        dynamodb.meta.client.transact_write_items(
            TransactItems=[
                {
                    'Update': {
                        'TableName': env['LINKS_TABLE'],
                        'Key': {'id': link_id},
                        **update_link_args(link_update, user)
                    },
                },
                {
                    'Put': {
                        'TableName': env['UNIQUES_TABLE'],
                        'Item': {
                            'type': 'backhalf',
                            'value': link_update.backhalf,
                            'link_id': link_id,
                        },
                        'ConditionExpression': 'attribute_not_exists(#t)',
                        'ExpressionAttributeNames': {'#t': 'type'},
                    },
                },
                {
                    'Delete': {
                        'TableName': env['UNIQUES_TABLE'],
                        'Key': {
                            'type': 'backhalf',
                            'value': old_backhalf,
                        },
                    },
                },
            ]
        )
        response = links_table.get_item(
            Key={
                'id': link_id,
            }
        )
        return as_link(response)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != 'TransactionCanceledException':
            raise
        if e.response['CancellationReasons'][0]['Code'] != 'None':
            raise NotOwnedByUserError
        raise LinkAlreadyExistsError


def delete_record(backhalf: str, user: str = None):
    if user is not None:
        user_condition = {
            'ConditionExpression': '#u = :u',
            'ExpressionAttributeNames': {'#u': 'user'},
            'ExpressionAttributeValues': {':u': user},
        }
    else:
        user_condition = dict()
    try:
        dynamodb.meta.client.transact_write_items(
            TransactItems=[
                {
                    'Delete': {
                        'TableName': env['LINKS_TABLE'],
                        'Key': {'id': get_link_id(backhalf)},
                        **user_condition,
                    },
                },
                {
                    'Delete': {
                        'TableName': env['UNIQUES_TABLE'],
                        'Key': {
                            'type': 'backhalf',
                            'value': backhalf,
                        },
                    },
                },
            ]
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != 'TransactionCanceledException':
            raise
        raise NotOwnedByUserError


def delete_all_records():
    # links
    scan = links_table.scan(
        FilterExpression=Attr('id').exists(),
    )
    with links_table.batch_writer() as batch:
        for each in scan['Items']:
            batch.delete_item(
                Key={
                    'id': each['id']
                }
            )
    # uniques
    scan = uniques_table.scan(
        FilterExpression=Attr('type').eq('backhalf'),
    )
    with uniques_table.batch_writer() as batch:
        for each in scan['Items']:
            batch.delete_item(
                Key={
                    'type': each['type'],
                    'value': each['value']
                }
            )


def set_redirect(link: Link):
    bucket.Object(link.backhalf).put(
        WebsiteRedirectLocation=link.origin,
        ACL='public-read'
    )


def unset_redirect(link: Union[Link, str]):
    bucket.Object(link.backhalf if type(link) is Link else link).delete()


def unset_all_redirects():
    bucket.objects.all().delete()


def is_taken(backhalf):
    try:
        bucket.Object(backhalf).load()
        return True
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        raise e


def update_item_params(data: Dict) -> Dict:
    return {
        'UpdateExpression': f'SET {", ".join(f"#p{i} = :v{i}" for i in range(len(data)))}',
        'ExpressionAttributeNames': {f'#p{idx}': name for (idx, name) in enumerate(data.keys())},
        'ExpressionAttributeValues': {f':v{idx}': value for (idx, value) in enumerate(data.values())},
    }


def update_link_args(link_update: LinkUpdate, user: str = None) -> Dict:
    p = update_item_params(link_update.asdict())
    if user is None:
        return p
    p['ConditionExpression'] = '#u = :u'
    p['ExpressionAttributeNames']['#u'] = 'user'
    p['ExpressionAttributeValues'][':u'] = user
    return p


def get_link_id(backhalf: str) -> int:
    response = uniques_table.get_item(
        Key={
            'type': 'backhalf',
            'value': backhalf
        }
    )
    if 'Item' not in response:
        raise LinkNotFoundError
    return response['Item']['link_id']


def get(backhalf: str) -> Link:
    i = links_table.get_item(
        Key={
            'backhalf': backhalf
        }
    )
    if 'Item' not in i:
        raise LinkNotFoundError
    return Link(**(i['Item']))


def as_link(response: Dict) -> Link:
    if 'Item' in response:
        link_data = response['Item']
    elif 'Attributes' in response:
        link_data = response['Attributes']
    else:
        link_data = response
    return Link(**link_data)


class NotOwnedByUserError(Exception):
    pass


class LinkAlreadyExistsError(Exception):
    pass


class LinkNotFoundError(Exception):
    pass
