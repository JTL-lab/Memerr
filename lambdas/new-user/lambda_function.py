from decimal import Decimal
import logging
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

REGION = 'us-east-1'
BUCKET_DOMAIN = 'https://memerr-memes.s3.amazonaws.com/'
dynamodb = boto3.resource('dynamodb', region_name=REGION)
table_user_info = dynamodb.Table('user-info')
# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Lambda Fx to CRUD user
    
    :param 
    :return: 
    """
    print(f'@lambda_handler: inputs {event}, {context}')


"""
# TEST

"""