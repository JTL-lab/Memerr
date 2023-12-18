from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

REGION = 'us-east-1'
BUCKET_DOMAIN = 'https://memerr-memes.s3.amazonaws.com/'
dynamodb = boto3.resource('dynamodb', region_name=REGION)
table_meme_data = dynamodb.Table('meme-data-new')
table_user_info = dynamodb.Table('user-info')

def create_meme_item(meme_id, caption, ml_caption, categories, humor_rating, relatability_rating, originality_rating):
    try:
        """
        # TEST
        meme_rating_item = {
            'meme_Id': 'd6f44db6-e947-465f-9537-e4f39547e66b_image_1295.jpg'
            'bucket_Image_source': 'https://memerr-memes.s3.amazonaws.com/d6f44db6-e947-465f-9537-e4f39547e66b_image_1295.jpg'
            'caption: 'Strange. Evil @CollegeMemes99 Me to Those 2 Person Who also Got 0 Number in Xams... Tum dono mere dost ho..'
            'ml_caption': 'a man with glasses is holding a camera'
            'categories': '"[very_funny, not_sarcastic, edgy, not_motivational, 'negative]"'
            'inserted_at_timestamp': '2023-11-20T16:57:06.715508'
            'num_ratings': 73 (needs to update the atomic counter field in dynamoDB)
            'humor_rating': 3.78
            'relatability_rating': 4.13
            'originality_rating': 4.57
        }
        """

        meme_rating_item={
            'meme_Id': meme_id,
            'bucket_Image_source': f'{BUCKET_DOMAIN}{meme_id}',
            'caption': caption,
            'ml_caption': ml_caption,
            'categories': categories,
            'humor_rating': Decimal(str(humor_rating)),
            'relatability_rating': Decimal(str(relatability_rating)),
            'originality_rating': Decimal(str(originality_rating)),
            # 'num_ratings': (needs to update the atomic counter field in dynamoDB)
        }
        response = table_meme_data.put_item(meme_rating_item)
        return response
    except ClientError as e:
        print(e.response['Error']['Message'])

def read_meme_item(meme_id):
    try:
        response = table_meme_data.get_item(Key={'meme_id': meme_id})
        return response.get('Item')  # Returns None if no item found
    except ClientError as e:
        print(e.response['Error']['Message'])

def update_meme_item(meme_id, new_humor_rating, new_num_ratings):
    try:
        response = table_meme_data.update_item(
            Key={'meme_id': meme_id},
            UpdateExpression="SET humor_rating = :hr, num_ratings = :nr",
            ExpressionAttributeValues={
                ':hr': new_humor_rating,
                ':nr': new_num_ratings
            },
            ReturnValues="UPDATED_NEW"
        )
        return response
    except ClientError as e:
        print(e.response['Error']['Message'])

def delete_meme_item(meme_id):
    try:
        response = table_meme_data.delete_item(Key={'meme_id': meme_id})
        return response
    except ClientError as e:
        print(e.response['Error']['Message'])

def lambda_handler(event, context):
    """
    Lambda Fx to CRUD meme_ratings
    
    :param Either a Profile object or date_of_birth
    :return: JSON object can_toggle_nsfw boolean True/False
    """
    print(f'@lambda_handler: inputs {event}, {context}')

    try:
        if event['httpMethod'] == 'POST':
            # create_meme_item()
            print('create_meme_item')
        elif event['httpMethod'] == 'GET':
            # read_meme_item()
            print('read_meme_item')
        elif event['httpMethod'] == 'PUT':
            # update_meme_item()
            print('update_meme_item')
        elif event['httpMethod'] == 'DELETE':
            # delete_meme_item()
            print('delete_meme_item')
        else:
            return {'statusCode': 400, 'body': 'Unsupported method'}
    except ValueError as e:
        return {"error": str(e)}

"""
# TEST
if __name__ == "__main__":
    test_event_item = {
        'meme_Id': 'd6f44db6-e947-465f-9537-e4f39547e66b_image_1295.jpg'
        'bucket_Image_source': 'https://memerr-memes.s3.amazonaws.com/d6f44db6-e947-465f-9537-e4f39547e66b_image_1295.jpg'
        'caption: 'Strange. Evil @CollegeMemes99 Me to Those 2 Person Who also Got 0 Number in Xams... Tum dono mere dost ho..'
        'ml_caption': 'a man with glasses is holding a camera'
        'categories': '"[very_funny, not_sarcastic, edgy, not_motivational, 'negative]"'
        'inserted_at_timestamp': '2023-11-20T16:57:06.715508'
        'num_ratings': 73 (needs to update the atomic counter field in dynamoDB)
        'humor_rating': 3.78
        'relatability_rating': 4.13
        'originality_rating': 4.57
    }
    print(lambda_handler(test_event_item, None))
"""