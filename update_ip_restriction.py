import json

import re
from abc import abstractmethod
from common import decorator, Dynamo, Quicksight, Logger

def create_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(body)
    }


def get_parameters_helper(dictionary, key, optional=False):
    if key in dictionary:
        return None, dictionary.get(key)
    if not optional:
        return json.dumps(f"{key} parameter is required"), None
    return None, None


def GetParameters(dictionary, *parameters):
    params = {}
    for item in parameters:
        err, val = get_parameters_helper(dictionary, item.key, item.optional)
        if err:
            return err, None
        params[item.key] = val
    return None, params


class Param:
    def __init__(self, key, optional=False):
        self.key = key
        self.optional = optional


class Handler:
    next_handler = None

    def set_next(self, handler):
        self.next_handler = handler
        return handler

    @abstractmethod
    def handle(self, parameters, err_msg_list, stop=False):
        print(f"-> Current Handler: {type(self).__name__} - {stop} ", end="")
        if stop:
            return stop, err_msg_list

        if self.next_handler:
            print(f"-> Next Handler: {type(self.next_handler).__name__} ")
            return self.next_handler.handle(parameters, err_msg_list, stop)

        return False, err_msg_list


class IPValidationHandler(Handler):

    @staticmethod
    def is_valid_ipv4(ip):
        ipv4_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
        if ipv4_pattern.match(ip):
            parts = ip.split('.')
            return all(0 <= int(part) <= 255 for part in parts)
        return False

    @staticmethod
    def is_parameter_valid(parameters):
        return parameters["ip"] is not None and IPValidationHandler.is_valid_ipv4(parameters["ip"])

    def handle(self, parameters, err_msg_list=None, allowed=False):
        if err_msg_list is None:
            err_msg_list = []
        is_parameter_valid = IPValidationHandler.is_parameter_valid(parameters)
        if not is_parameter_valid:
            print(f"IP is not valid for {type(self).__name__}")
            err_msg_list.append("IP is invalid")
        return super().handle(parameters, err_msg_list, not is_parameter_valid)


def list_to_multiline_str(value: list) -> str:
    return "\n".join(value)


@decorator
def validation(**validation_parameters):
    # VALIDATION
    validation_handler = IPValidationHandler()
    is_invalid, unaccepted_validation_handler_messages = validation_handler.handle(validation_parameters)
    if is_invalid:
        err = list_to_multiline_str(unaccepted_validation_handler_messages)
        return err
    return None


@decorator
def update_ip_restriction(username, duration, ip):
    err = None

    try:

        # Validation
        err = validation(ip=ip)

        if err is not None:
            return

        ip = f"{ip}/32"

        # Dynamo Table Creation
        Dynamo.create_dynamodb_table()

        Quicksight.update_ip_restrictions(username=username, ip=ip, delete=False)

        Dynamo.save_access(username, duration, ip)

    except Exception as error:
        Logger.get_logger().error(error)
        err = error
    finally:
        if err is not None:
            return "access NOT granted, reason: " + str(err)
        else:
            return "access granted"


# Lambda Handler
def lambda_handler(event, context):
    request = event.get("body")

    # PARAMETERS Validation
    error, parameters = GetParameters(request,
                                      Param("ip"),
                                      Param("username"),
                                      Param("duration"))

    if error is not None:
        Logger.get_logger().error(error)
        return create_response(500, error)

    try:
        result = update_ip_restriction(**parameters)
        if result != "access granted":
            raise Exception(f"{result}")
    except Exception as e:
        print(f"Error during ip restriction creation: {e}")
        return create_response(500, f"IP restriction creation failed. Error: {str(e)}")

    return create_response(200, result)


# Main Entry Point
if __name__ == '__main__':
    event = {
        "body": {
            "username": "muhammed.kaya",
            "duration": "24",
            "ip": ""
        }
    }
    lambda_handler(event, None)
