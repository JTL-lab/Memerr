from decimal import Decimal
import logging
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

# Constants for the DynamoDB table and the AWS region
REGION = 'us-east-1'
TABLE_NAME = 'user-info'
dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class UserInfoItem:
    def __init__(self, email, dob, is_nsfw, memes_posted, memes_rated, memes_saved, phone):
        self.email = email
        self.dob = dob
        self.is_nsfw = is_nsfw
        self.memes_posted = memes_posted
        self.memes_rated = memes_rated
        self.memes_saved = memes_saved
        self.phone = phone

    def to_dynamo_dict(self):
        """Convert the user info item to a dictionary suitable for DynamoDB."""
        return {
            'email': self.email,
            'dob': self.dob,
            'is_nsfw': self.is_nsfw,
            'memes_posted': self.memes_posted,
            'memes_rated': self.memes_rated,
            'memes_saved': self.memes_saved,
            'phone': self.phone
        }

    def create_user_item(self):
        try:
            user_item = self.to_dynamo_dict()
            response = table.put_item(
                Item=user_item,
                ConditionExpression='attribute_not_exists(email)'
            )
            logger.info(f"User item with email {self.email} created successfully.")
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == "ConditionalCheckFailedException":
                logger.info(f"User with email {self.email} already exists.")
            else:
                logger.error(e.response['Error']['Message'])
            return None

    def read_user_item(self):
        try:
            response = table.get_item(Key={'email': self.email})
            return response.get('Item')
        except ClientError as e:
            logger.error(e.response['Error']['Message'])
            return None

    def update_user_item(self, new_memes_rated):
        try:
            response = table.update_item(
                Key={'email': self.email},
                UpdateExpression='SET memes_rated = :mr',
                ExpressionAttributeValues={
                    ':mr': new_memes_rated
                },
                ReturnValues='UPDATED_NEW'
            )
            logger.info(f"User item with email {self.email} updated successfully.")
            return response
        except ClientError as e:
            logger.error(e.response['Error']['Message'])
            return None

    def delete_user_item(self):
        try:
            response = table.delete_item(Key={'email': self.email})
            logger.info(f"User item with email {self.email} deleted successfully.")
            return response
        except ClientError as e:
            logger.error(e.response['Error']['Message'])
            return None


"""
# Usage
user_item = UserItem(
    'email': self.email,
    'dob': self.dob,
    'is_nsfw': self.is_nsfw,
    'memes_posted': self.memes_posted,
    'memes_rated': self.memes_rated,
    'memes_saved': self.memes_saved,
    'phone': self.phone
)

user_item_dict = user_item.to_dynamo_dict()
"""