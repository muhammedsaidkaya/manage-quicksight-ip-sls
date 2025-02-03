import time
from common import decorator, Logger, Dynamo, Quicksight


@decorator
def check_item_is_expired(item):
    expire_time = item['expireTime'].get('N')
    return int(expire_time) < int(time.time())


def find_expired_users():
    items = Dynamo.find_expired_users()
    for item in items:
        if check_item_is_expired(item):
            try:
                remove_ip_restriction(dynamo_item=item)
            except Exception as e:
                raise e


@decorator
def remove_ip_restriction(dynamo_item):
    try:
        username = dynamo_item['username'].get('S')
        ip = dynamo_item['ip'].get('S')
        Quicksight.update_ip_restrictions(username=username, ip=ip, delete=True)
        dynamo_item['deleted'] = {'N': str(1)}
        Dynamo.put_item(dynamo_item)
    except Exception as error:  # raise all exceptions to create CW alert
        raise error


if __name__ == '__main__':
    find_expired_users()


def lambda_handler(event, context):
    return find_expired_users()
