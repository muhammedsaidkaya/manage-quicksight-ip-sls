import boto3
import os
import time
from common.logging import Logger, decorator
import uuid


class Dynamo:
    DYNAMODB_CLIENT = boto3.client('dynamodb', region_name=os.environ['AWS_REGION'])
    DYNAMODB_TABLE_NAME = "quicksight-ips-v1"

    @staticmethod
    def find_expired_users():
        result = Dynamo.DYNAMODB_CLIENT.query(
            TableName=Dynamo.DYNAMODB_TABLE_NAME,
            IndexName='deleted-username-gsi',
            KeyConditions={
                'deleted': {
                    'AttributeValueList': [
                        {
                            'N': '0',
                        },
                    ],
                    'ComparisonOperator': 'EQ'
                }
            }
        )
        items = result.get('Items')
        return items

    @staticmethod
    def put_item(item):
        Dynamo.DYNAMODB_CLIENT.put_item(TableName=Dynamo.DYNAMODB_TABLE_NAME, Item=item)

    @staticmethod
    @decorator
    def create_dynamodb_table():
        try:
            Dynamo.DYNAMODB_CLIENT.create_table(
                AttributeDefinitions=[
                    {
                        'AttributeName': 'id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'username',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'deleted',
                        'AttributeType': 'N'
                    }
                ],
                TableName=Dynamo.DYNAMODB_TABLE_NAME,
                KeySchema=[
                    {
                        'AttributeName': 'id',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'username',
                        'KeyType': 'RANGE'
                    },
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'deleted-username-gsi',
                        'KeySchema': [
                            {
                                'AttributeName': 'deleted',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'username',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 2,
                            'WriteCapacityUnits': 2
                        }
                    },
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 1,
                    'WriteCapacityUnits': 1
                }
            )
        except Dynamo.DYNAMODB_CLIENT.exceptions.ResourceInUseException:
            pass
        except Exception as e:
            Logger.get_logger().error(e)
            pass

    @staticmethod
    def get_active_item_by_username(username):
        expression_attribute_values = {':username': {'S': username}, ':deleted': {'N': str(0)}}
        filter_expression = 'username = :username AND deleted = :deleted'
        result = Dynamo.DYNAMODB_CLIENT.scan(
            TableName=Dynamo.DYNAMODB_TABLE_NAME,
            FilterExpression=filter_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        items = result.get('Items')
        while True:
            if 'LastEvaluatedKey' in result:
                exclusive_start_key = result['LastEvaluatedKey']
                result = Dynamo.DYNAMODB_CLIENT.scan(
                    TableName=Dynamo.DYNAMODB_TABLE_NAME,
                    FilterExpression=filter_expression,
                    ExclusiveStartKey=exclusive_start_key,
                    ExpressionAttributeValues=expression_attribute_values
                )
                items += result.get('Items')
            else:
                break
        return items

    @staticmethod
    def save_access(username, duration, ip):
        # Get previous Dynamo items
        items = Dynamo.get_active_item_by_username(username)

        # If Dynamo Item Already Exists, Then Update IP Column
        if len(items) > 0:
            for item in items:
                item["ip"] = {'S': ip}
                Dynamo.put_item(item)
            return

        # If Dynamo Item Does not Exist, Create New Record
        expire_time = int(time.time() + (int(duration) * 3600))
        Dynamo.put_item({
            'id': {'S': str(uuid.uuid4())},
            'username': {'S': username},
            'expireTime': {'N': str(expire_time)},
            'deleted': {'N': str(0)},
            'ip': {'S': str(ip)}
        })