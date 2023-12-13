"""
Helper script used to populate meme-data table with memes from Memotion dataset.
"""

import pandas as pd
import boto3
from datetime import datetime
import uuid

# Define credentials and region: replace with real credentials from AWS!
aws_access_key_id = ''
aws_secret_access_key = ''
region_name = 'us-east-1'

if __name__ == '__main__':

    # Read the CSV file
    df = pd.read_csv('labels.csv')

    # Initialize Boto3 S3 and DynamoDB clients
    s3_client = boto3.client('s3')
    dynamodb = dynamodb = boto3.resource('dynamodb', aws_access_key_id=aws_access_key_id,
                                         aws_secret_access_key=aws_secret_access_key, region_name=region_name)
    table = dynamodb.Table('meme-data')

    for index, row in df.iterrows():
        if index > 120:
            # Generate unique identifier
            unique_id = str(uuid.uuid4())
            new_filename = unique_id + '_' + row['image_name']

            # Upload image to S3
            s3_client.upload_file('images/' + row['image_name'], 'memerr-memes', new_filename,
                                  ExtraArgs={'ACL': 'public-read'})

            categories = '['
            for col in ['humour', 'sarcasm', 'offensive', 'motivational', 'overall_sentiment']:
                # Sarcasm metadata modifications for clarity
                if col == 'sarcasm' and row[col] == 'slight':
                    categories += 'mild sarcasm'
                elif col == 'sarcasm' and row[col] == 'general':
                    categories += 'sarcasm_free'

                # Offensiveness metadata modifications for clarity
                elif col == 'offensive' and row[col] == 'slight':
                    categories += 'edgy'
                elif col == 'offensive' and row[col] == 'very_offensive' or row[col] == 'hateful_offensive':
                    categories += 'nsfw'
                elif col == 'offensive' and row[col] == 'not_offensive':
                    categories += 'sfw'
                else:
                    categories += row[col]

                if col != 'overall_sentiment':
                    categories += ', '
                else:
                    categories += ']'

            # Prepare data for DynamoDB
            data = {
                'meme_id': new_filename,
                'inserted_at_timestamp': datetime.now().isoformat(),
                'categories': categories,
                'caption': row['text_corrected'],
                'ratings': [],
                'humor_rating': 0,
                'originality_rating': 0,
                'relatability_rating': 0,
                'bucket_image_source': 'https://memerr-memes.s3.amazonaws.com/' + new_filename
            }

            # Insert data into DynamoDB
            try:
                table.put_item(Item=data)
            except TypeError:
                pass
