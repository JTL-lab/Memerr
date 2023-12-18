import json
import logging
from memedata.meme_data_item import MemeDataItem

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        meme_data_item = MemeDataItem(
            meme_id=event['meme_id'],
            bucket_image_source=event['bucket_image_source'],
            caption=event['caption'],
            ml_caption=event['ml_caption'],
            categories=event['categories'],
            humor_rating=event['humor_rating'],
            relatability_rating=event['relatability_rating'],
            originality_rating=event['originality_rating'],
            num_ratings=event['num_ratings']
        )

        # Create the meme item in the DynamoDB table
        create_response = meme_data_item.create_meme_item()

        # Check if the create operation was successful
        if create_response:
            logger.info(f"Successfully created meme item: {event['meme_id']}")
            return {
                'statusCode': 200,
                'body': json.dumps('Successfully created meme item')
            }
        else:
            logger.error(f"Failed to create meme item: {event['meme_id']}")
            return {
                'statusCode': 400,
                'body': json.dumps('Failed to create meme item')
            }

    except KeyError as e:
        # Log the error if a required field is missing in the event data
        logger.error(f"KeyError: {str(e)} - The event data is missing a required field.")
        return {
            'statusCode': 400,
            'body': json.dumps(f"Missing data for required field: {str(e)}")
        }
    except Exception as e:
        # Log any other exception that occurs
        logger.error(f"An error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"An error occurred: {str(e)}")
        }


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