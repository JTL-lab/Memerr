import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

# Constants for the S3 bucket and DynamoDB table
BUCKET_DOMAIN = "https://your-s3-bucket-name.s3.amazonaws.com/"
DYNAMODB_TABLE_NAME = "meme-data-new"

# Initialize a DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE_NAME)


class MemeRatingItem:
    def __init__(self, meme_id, caption, ml_caption, categories, humor_rating, relatability_rating, originality_rating):
        self.meme_id = meme_id
        self.bucket_image_source = f'{BUCKET_DOMAIN}{meme_id}'
        self.caption = caption
        self.ml_caption = ml_caption
        self.categories = categories
        self.humor_rating = Decimal(str(humor_rating))
        self.relatability_rating = Decimal(str(relatability_rating))
        self.originality_rating = Decimal(str(originality_rating))
        self.num_ratings = 1  # Default to 1 for a new rating

"""
class MemeRatings:
    def __init__(self, meme_id):
        self.meme_id = meme_id
        self.meme_ratings = []

    def add_meme_rating(self, meme_rating):
        self.meme_ratings.append(meme_rating)

    def get_all_ratings(self):
        return self.meme_ratings


class MemeRating:
    def __init__(self, meme_rating_id, ratings_by_category):
        self.meme_rating_id = meme_rating_id
        self.ratings_by_category = ratings_by_category


class RatingsByCategory:
    def __init__(self, humor, originality, relatability):
        self.humor = humor
        self.originality = originality
        self.relatability = relatability
"""