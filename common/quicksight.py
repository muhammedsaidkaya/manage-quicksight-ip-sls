import json
import os

import boto3
from common.logging import decorator, Logger


class Quicksight:
    QUICKSIGHT_CLIENT = boto3.client("quicksight", "us-east-1")
    ACCOUNT_ID = os.getenv("ACCOUNT_ID")

    @staticmethod
    @decorator
    def describe_ip_restrictions_with_pagination():
        """
        Retrieve all IP restriction rules for an AWS QuickSight account, handling pagination.
        """
        ip_restriction_map = {}
        try:

            # Make the API call with NextToken (if present)
            response = Quicksight.QUICKSIGHT_CLIENT.describe_ip_restriction(
                AwsAccountId=Quicksight.ACCOUNT_ID
            )

            # Merge the current page's rules into the overall map
            ip_restriction_map.update(response.get('IpRestrictionRuleMap', {}))

            Logger.get_logger().info("Complete IP Restrictions: " + json.dumps(ip_restriction_map, indent=4))
            return ip_restriction_map
        except Exception as e:
            Logger.get_logger().error(f"Error describing IP restrictions: {e}")
            raise Exception(f"Error describing IP restrictions: {e}")

    @staticmethod
    @decorator
    def update_ip_restrictions(username, ip, delete=False):
        """
        Update IP restriction rules for an AWS QuickSight account.
        """
        try:

            ip_rules = Quicksight.describe_ip_restrictions_with_pagination()

            if delete:
                # Filter
                ip_rules = {k: v for k, v in ip_rules.items() if k != ip or v != username}
            else:
                # If Already User Exists, Filter Old Record
                ip_rules = {k: v for k, v in ip_rules.items() if v != username}
                ip_rules[ip] = username

            Logger.get_logger().info("IP Rules: " + str(ip_rules))

            response = Quicksight.QUICKSIGHT_CLIENT.update_ip_restriction(
                AwsAccountId=Quicksight.ACCOUNT_ID,
                IpRestrictionRuleMap=ip_rules,
                Enabled=True
            )
            Logger.get_logger().info("IP Restrictions updated successfully: " + str(response))
            return response

        except Exception as e:
            raise Exception(f"Error while updating IP restrictions: {e}")
