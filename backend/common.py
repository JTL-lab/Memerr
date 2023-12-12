import os
import logging
import json
import time
import boto3
from botocore.exceptions import ClientError


#region Global Variables
OS_ENV = "America/New_York"
REGION_NAME='us-east-1'
DOMAIN_NAME = ''
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
#endregion

''' 
Resources
- DB: user profile; memes; 
- 
'''

def get_user_profile(uid):
    user_profile = None
    # call AWS DynamoDB to get user_profile by uid
    return user_profile

def is_nsfw_user(user):
    print(f'@is_nsfw: {user}')
    
    # if the user age < 18, return false
    is_nsfw_user = False
    return is_nsfw_user

def get_memes_nsfw():
    print(f'@get_memes_nsfw: ')
    memes = []
    return memes

def get_memes_sfw():
    print(f'@get_memes_sfw: ')
    memes = []
    return memes
