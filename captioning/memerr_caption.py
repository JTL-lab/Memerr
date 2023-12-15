import boto3
import json
import logging
import base64

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def process_all_images():
    s3 = boto3.client('s3')
    try:
        # List objects in the specified bucket
        response = s3.list_objects_v2(Bucket='memerr-memes')

        # Print the list of objects
        if 'Contents' in response:
            for idx, obj in enumerate(response['Contents']):
                object_key = obj['Key']

                if idx > 157 and 'jpg' or 'png' in object_key.lower():
                    img_response = s3.get_object(Bucket='memerr-memes', Key=object_key)
                    image_data = img_response['Body'].read()
                    base64_image = base64.b64encode(image_data).decode('utf-8')
                    result = process_image(base64_image)
                    store_result = {
                        "image_name": object_key,
                        "caption": result
                    }
                    metadata_key = object_key.split('.')[0] + ".json"
                    s3.put_object(Bucket='memerr-metadata', Key=metadata_key, 
                                  Body = json.dumps(store_result), ContentType='json')
        else:
            print("No objects found in the bucket.")

        return {
            'statusCode': 200,
            'body': 'Lambda function executed successfully'
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }

def process_image(base64_image):
    input_data = {"inputs": [base64_image]}
    runtime= boto3.client('runtime.sagemaker')
    
    response = runtime.invoke_endpoint(EndpointName="huggingface-pytorch-inference-2023-12-15-21-16-41-656",
                                       ContentType='application/json',
                                       Body=json.dumps(input_data))
    
    result = str(response['Body'].read().decode('utf-8'))
    result = result.split('"')[2]
    result = result.replace("\\", "")
    print(result)
    return result


def lambda_handler(event, context):
    print("Verify the branch work")
    
    # # Already DONE for 250 images!!!
    # print("Generate captions for all the existing images once")
    # response = process_all_images()
    # return response

    # Triggered when an image is uploaded to the S3 bucket
    try:
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        photo_name = event['Records'][0]['s3']['object']['key']
        # print(bucket_name, photo_name)
        s3 = boto3.client('s3')
        if 'jpg' or 'png' in photo_name.lower():
            img_response = s3.get_object(Bucket=bucket_name, Key=photo_name)
            image_data = img_response['Body'].read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            result = process_image(base64_image)
            store_result = {
                "image_name": photo_name,
                "caption": result
            }
            metadata_key = photo_name.split('.')[0] + ".json"
            s3.put_object(Bucket='memerr-metadata', Key=metadata_key, 
                            Body = json.dumps(store_result), ContentType='json')
        response = "Uploaded captions to S3 bucket successfully"
    except:
        response = "Issue with uploading captions to S3 bucket"

    print(response)
    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
