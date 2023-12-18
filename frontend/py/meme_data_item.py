from decimal import Decimal
import logging
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

REGION = 'us-east-1'
BUCKET_DOMAIN = 'https://memerr-memes.s3.amazonaws.com/'
dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table('meme-data-new')
# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Utility function to log and raise exceptions
def handle_exception(e):
    logger.error(f"An error occurred: {str(e)}")
    raise Exception(f"An error occurred: {str(e)}")
def check_is_duplicate_item(key, value):
    # Check if meme_id already exists to avoid overwriting
    response = table.get_item(Key={key: value})
    if 'Item' in response:
        logger.info(f"{key} item with ID {value} already exists.")
        return {'message': 'Item already exists.'}

class MemeDataItem:
    def __init__(self, meme_id, bucket_image_source, caption, ml_caption, categories, humor_rating, relatability_rating, originality_rating, num_ratings):
        self.meme_id = meme_id
        self.bucket_image_source = bucket_image_source
        self.caption = caption
        self.ml_caption = ml_caption
        self.categories = categories
        self.humor_rating = Decimal(str(humor_rating))
        self.relatability_rating = Decimal(str(relatability_rating))
        self.originality_rating = Decimal(str(originality_rating))
        self.num_ratings = num_ratings

    def to_dynamo_dict(self):
        """Convert the meme rating item to a dictionary suitable for DynamoDB."""
        return {
            'meme_Id': self.meme_id,
            'bucket_Image_source': self.bucket_image_source,
            'caption': self.caption,
            'ml_caption': self.ml_caption,
            'categories': self.categories,
            'humor_rating': self.humor_rating,
            'relatability_rating': self.relatability_rating,
            'originality_rating': self.originality_rating,
            'num_ratings': self.num_ratings
        }

    # Create Meme Item
    def create_meme_item(self):
        try:
            # Check if meme_id already exists to avoid overwriting
            response = table.get_item(Key={'meme_Id': self.meme_id})
            if 'Item' in response:
                logger.info(f"Meme item with ID {self.meme_id} already exists.")
                return {'message': 'Item already exists.'}

            # Create new meme item
            meme_item = self.to_dynamo_dict()  # Call the method to get the dictionary
            response = table.put_item(
                Item=meme_item,
                ConditionExpression='attribute_not_exists(meme_Id)'
            )
            logger.info(f"Meme item with ID {self.meme_id} created successfully.")
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == "ConditionalCheckFailedException":
                logger.info(f"Meme rating for {self.meme_id} already exists.")
            else:
                logger.error(e.response['Error']['Message'])
            return None
        except Exception as e:
            handle_exception(e)

    # Update Meme Item
    def update_meme_item(self, new_humor_rating, new_relatability_rating, new_originality_rating):
        try:
            update_expression = 'SET humor_rating = :h, relatability_rating = :r, originality_rating = :o ADD num_ratings :incr'
            response = table.update_item(
                Key={'meme_Id': self.meme_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues={
                    ':h': Decimal(str(new_humor_rating)),  # Convert to Decimal
                    ':r': Decimal(str(new_relatability_rating)),  # Convert to Decimal
                    ':o': Decimal(str(new_originality_rating)),  # Convert to Decimal
                    ':incr': 1
                },
                ReturnValues='UPDATED_NEW'
            )
            logger.info(f"Meme item with ID {self.meme_id} updated successfully.")
            return response
        except ClientError as e:
            logger.error(e.response['Error']['Message'])
            return None
        except Exception as e:
            handle_exception(e)

    # Read Meme Item
    def read_meme_item(self):
        try:
            response = table.get_item(Key={'meme_id': self.meme_id})
            item = response.get('Item')
            if item:
                logger.info(f"Meme item with ID {self.meme_id} retrieved successfully.")
            else:
                logger.info(f"Meme item with ID {self.meme_id} not found.")
            return item
        except ClientError as e:
            print(e.response['Error']['Message'])
            return None
        except Exception as e:
            handle_exception(e)

    # Delete Meme Item
    def delete_meme_item(self):
        try:
            response = table.delete_item(Key={'meme_id': self.meme_id})
            logger.info(f"Meme item with ID {self.meme_id} deleted successfully.")
            return response
        except ClientError as e:
            print(e.response['Error']['Message'])
            return None
        except Exception as e:
            handle_exception(e)

"""
# Usage
meme_data_item = MemeDataItem(
    meme_id='d6f44db6-e947-465f-9537-e4f39547e66b_image_1295.jpg',
    bucket_image_source='https://memerr-memes.s3.amazonaws.com/d6f44db6-e947-465f-9537-e4f39547e66b_image_1295.jpg',
    caption='Strange. Evil @CollegeMemes99 Me to Those 2 Person Who also Got 0 Number in Xams... Tum dono mere dost ho..',
    ml_caption='a man with glasses is holding a camera',
    categories='[very_funny, not_sarcastic, edgy, not_motivational, negative]',
    humor_rating=3.78,
    relatability_rating=4.13,
    originality_rating=4.57,
    num_ratings=73  # assuming you're handling the atomic increment elsewhere
)

meme_data_item_dict = meme_data_item.to_dynamo_dict()
"""