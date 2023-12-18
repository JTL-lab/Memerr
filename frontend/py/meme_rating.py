import json
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

class UserInfoManager:
    def __init__(self, table_name, user_email):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
        self.user_email = user_email

    def get_user_info(self):
        try:
            response = self.table.get_item(Key={'email': self.user_email})
            return response.get('Item')
        except ClientError as e:
            print(f"Could not get user info: {e.response['Error']['Message']}")
            return None

    def update_memes_posted(self, new_memes_posted):
        user_info = self.get_user_info()
        if user_info:
            # Combine old and new memes_posted lists, ensuring no duplicates
            updated_memes_posted = list(set(user_info.get('memes_posted', []) + new_memes_posted))
            try:
                self.table.update_item(
                    Key={'email': self.user_email},
                    UpdateExpression="SET memes_posted = :mp",
                    ExpressionAttributeValues={':mp': updated_memes_posted}
                )
                print(f"Updated memes_posted for user {self.user_email}.")
            except ClientError as e:
                print(f"Could not update memes_posted: {e.response['Error']['Message']}")

    def update_memes_rated(self, meme_id, ratings):
        user_info = self.get_user_info()
        if user_info:
            # Ensure existing ratings are retained and new ones are added or updated
            updated_memes_rated = user_info.get('memes_rated', {})
            updated_memes_rated[meme_id] = ratings
            try:
                self.table.update_item(
                    Key={'email': self.user_email},
                    UpdateExpression="SET memes_rated = :mr",
                    ExpressionAttributeValues={':mr': updated_memes_rated}
                )
                print(f"Updated memes_rated for user {self.user_email}.")
            except ClientError as e:
                print(f"Could not update memes_rated: {e.response['Error']['Message']}")

    def update_memes_saved(self, new_memes_saved):
        user_info = self.get_user_info()
        if user_info:
            # Combine old and new memes_saved lists, ensuring no duplicates
            updated_memes_saved = list(set(user_info.get('memes_saved', []) + new_memes_saved))
            try:
                self.table.update_item(
                    Key={'email': self.user_email},
                    UpdateExpression="SET memes_saved = :ms",
                    ExpressionAttributeValues={':ms': updated_memes_saved}
                )
                print(f"Updated memes_saved for user {self.user_email}.")
            except ClientError as e:
                print(f"Could not update memes_saved: {e.response['Error']['Message']}")
"""
# TEST
user_info_manager = UserInfoManager(table_name='user-info', user_email='user@example.com')

# Update memes_posted
new_memes_posted = ['new_image_1.jpg', 'new_image_2.png']
user_info_manager.update_memes_posted(new_memes_posted)

# Update memes_rated
meme_id = 'new_meme_id'
ratings = {'humor_rating': '5', 'originality_rating': '5', 'relatability_rating': '5'}
user_info_manager.update_memes_rated(meme_id, ratings)

# Update memes_saved
new_memes_saved = ['new_saved_image_1.png', 'new_saved_image_2.jpg']
user_info_manager.update_memes_saved(new_memes_saved)
"""