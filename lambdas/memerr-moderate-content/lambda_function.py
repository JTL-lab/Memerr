import os
import logging
import json
import hashlib
import time
from datetime import datetime
import boto3
import botocore
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from requests_aws4auth import AWS4Auth

REGION = 'us-east-1'
BUCKET_NAME = 'memerr-memes'
REKOGNITION_ARN = 'arn:aws:rekognition:us-east-1:756963467680:project/Meme-Moderation-Classifier/version/Meme-Moderation-Classifier.2023-12-12T19.21.58/1702426918663'

def detect_labels(bucket, photo):
    print(f'@detect_labels: {bucket}, {photo}')
    image = {
                'S3Object': {
                    'Bucket': bucket,
                    'Name': photo,
                }
            }
                     
    try:
        
        # Start the Rekognition custom label model
        client_rekognition.start_project_version(ProjectVersionArn=REKOGNITION_ARN, MinInferenceUnits=1)
            
        # Detect labels with running model 
        response = client_rekognition.detect_labels(Image=image, MaxLabels=10)
        print(f'rekognition_response: {response}')
        labels = response.get('Labels', [])
        labels_lowercase = [label['Name'].lower() for label in labels]
            
    except (BotoCoreError, ClientError) as error:
        logger.error('Error %s: @detect_labels: bucket %s, photo %s', error, bucket, photo)
        raise
        
    return labels_lowercase


def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    auth = AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)
    return auth
    

def remove_photo(bucket, photo_name):
    s3_client = boto3.client('s3', region_name=REGION)
    try:
        # Delete the photo from the S3 bucket
        s3_client.delete_object(Bucket=bucket, Key=photo_name)
        return {
            'statusCode': 200,
            'body': f'Image {photo_name} has been removed from the bucket {bucket}.'
        }
    except Exception as e:
        logger.error('Error deleting photo %s from bucket %s: %s', photo_name, bucket, str(e))
        return {
            'statusCode': 500,
            'body': f'Error deleting image {photo_name} from the bucket {bucket}: {str(e)}'
        }


def lambda_handler(event, context):
    # print('@lambda_handler: event', event)
    
    # 1) Get new image details 
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    print(bucket_name)
    image_name = event['Records'][0]['s3']['object']['key']
    print(image_name)
    
    # 2) Call upon Rekognition model to detect new labels 
    # Documentation: https://docs.aws.amazon.com/rekognition/latest/customlabels-dg/ex-lambda.html#example-lambda-add-code
    image_labels = detect_labels(bucket_name, image_name)
    
    # 3) If image receives 'hateful' label, we remove it from the bucket
    if 'hateful' in image_labels:
        remove_photo(bucket_name, image_name)
    
    return index_response

