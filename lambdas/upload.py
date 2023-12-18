import json
import logging
import base64
import boto3
from boto3.dynamodb.conditions import Key
import json
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection
import datetime
import random
import boto3
from boto3.dynamodb.conditions import Key


class DynamoDB:
    def __init__(self, region_name:str, dynamo_db_table:str):
        # Replace 'your-region' and 'your-dynamodb-table' with your actual AWS region and DynamoDB table name
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.table = self.dynamodb.Table(dynamo_db_table)

    def scan_all_items(self):
        items = []
        last_evaluated_key = None

        while True:
            if last_evaluated_key:
                response = self.table.scan(ExclusiveStartKey=last_evaluated_key)
            else:
                response = self.table.scan()

            items.extend(response.get('Items', []))
            last_evaluated_key = response.get('LastEvaluatedKey')

            if not last_evaluated_key:
                break

        print("yooo ", len(items))
        return items


    def get_memes_data(self):
        response = self.table.scan()
        memes_data = response.get('Items', [])
        return memes_data
    
    def query_single(self, query_id, primary_key):
        
        response = self.table.query(
                KeyConditionExpression=Key(primary_key).eq(query_id)
            )
        data = response.get('Items', [])
        return data

    def retrieve_memes(self, query_ids, primary_key):
        
        memes_data = []
        for query_id in query_ids:
            response = self.table.query(
                KeyConditionExpression=Key(primary_key).eq(query_id)
            )
            items = response.get('Items', [])
            memes_data.extend(items)

        return memes_data


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

index_name = "memerrsearch"
opensearch_url = "search-memerrsearch-hbgsqydnohjzfv26vjj4h3wi44.us-east-1.es.amazonaws.com"
opensearch_region = "us-east-1"

def get_es_client(host=opensearch_url,
    port=443,
    region=opensearch_region,
    index_name=index_name
    ):

    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key,
                       credentials.secret_key,
                       region,
                       'es',
                       session_token=credentials.token)

    headers = {"Content-Type": "application/json"}

    es = Elasticsearch(hosts=[{'host': host, 'port': port}],
                       http_auth=awsauth,
                       use_ssl=True,
                       verify_certs=True,
                       connection_class=RequestsHttpConnection,
                       timeout=60 # for connection timeout errors
    )
    return es
    
def create_img_index(img_embedding, metadata_key):
    index_name = "memerrsearch"
    es = get_es_client()
    body = {}
    body['embeddings'] = img_embedding
    body['image_name'] = metadata_key
    try:
        es.index(index=index_name, id=metadata_key, doc_type='_doc', body=body)
    except Exception as e:
        print(e)
        
    return

def create_text_index(text_embedding, metadata_key):
    index_name = "textsearch"
    es = get_es_client()
    body = {}
    body['embeddings'] = text_embedding
    body['image_name'] = metadata_key
    try:
        es.index(index=index_name, id=metadata_key, doc_type='_doc', body=body)
    except Exception as e:
        print(e)
        
    return
    

def clip_process_all_images():
    s3 = boto3.client('s3')
    print("now line 1")
    try:
        # List objects in the specified bucket
        print("now line 2")
        response = s3.list_objects_v2(Bucket='memerr-memes')
        print("now line 3")
        # Print the list of objects
        print(len(response['Contents']))
        if 'Contents' in response:
            for idx, obj in enumerate(response['Contents']):
                object_key = obj['Key']
                # break
                if 'jpg' or 'png' in object_key.lower():
                    print("now line 4")
                    img_response = s3.get_object(Bucket='memerr-memes', Key=object_key)
                    image_data = img_response['Body'].read()
                    # print("now line 5")
                    # base64_image = base64.b64encode(image_data).decode('utf-8')
                    result = get_clip_embedding(image_data)
                    store_result = {
                        "image_name": object_key,
                        "embedding": result
                    }
                    metadata_key = object_key.split('.')[0] + ".json"
                    s3.put_object(Bucket='memerr-embeddingdata', Key=metadata_key, 
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


def s3_caption(photo, bucket):
    s3_client = boto3.client("s3")
    data = s3_client.head_object(Bucket=bucket, Key=photo)
    print(data)
    # extract custom labels if present
    try:
        customLabels = json.loads(data['ResponseMetadata']['HTTPHeaders']['x-amz-meta-customlabels'])
        description, tags = customLabels["description"], customLabels["tags"]
    except:
        description, tags = "", ""

    # print(customLabels)
    return description, tags


def get_clip_embedding(base64_image):
    # input_data = {"inputs": [base64_image]}
    runtime= boto3.client('runtime.sagemaker')

    response = runtime.invoke_endpoint(EndpointName="clip-image-model-2023-12-16-05-24-41-263",
                                       ContentType='application/x-image',
                                       Body=base64_image)#json.dumps(input_data))
    
    result = str(response['Body'].read())
    result = json.loads(eval(result))[0]
    # print(result)
    return result
    
    
def get_clip_text_embedding(query_text):
    input_data = {"inputs": query_text}
    runtime= boto3.client('runtime.sagemaker')

    response = runtime.invoke_endpoint(EndpointName="clip-text-model-2023-12-16-05-20-21-704",
                                       ContentType='application/json',
                                       Body=json.dumps(input_data))
    
    result = str(response['Body'].read())
    emb = json.loads(eval(result))[0]
    return emb


# Function to insert data into DynamoDB
def insert_data(meme):
    
    DYNAMODB_REGION = 'us-east-1'
    DYNAMODB_TABLE = 'meme-data-new'

    
    dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_REGION)
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    item = {
        'meme_id': meme[0],
        'bucket_image_source': meme[1],
        'caption': meme[2],
        'categories': meme[3],
        'humor_rating': str(round(random.uniform(3, 5), 2)),
        'inserted_at_timestamp': str(datetime.datetime.now()),
        'originality_rating': str(round(random.uniform(3, 5), 2)),
        'num_ratings': str(random.randint(15, 80)),
        'relatability_rating': str(round(random.uniform(3, 5), 2)),
        'ml_caption': meme[4],
    }

    response = table.put_item(Item=item)

from tqdm import tqdm
    
def opensearch_indexing_on_all_images():
    start_index = 0
    end_index   = 1000
    meme_table = DynamoDB("us-east-1","meme-data")
    # memes_data = meme_table.get_memes_data()
    memes_data = meme_table.scan_all_items()[start_index:end_index]
    s3 = boto3.client('s3')
    
    print(len(memes_data))
    for idx, data in tqdm(enumerate(memes_data)):
        
        bucket_name = 'memerr-memes'
        photo_name =  data['bucket_image_source'].split('com/')[1]
        
        if 'jpg' or 'png' in photo_name.lower():
            img_response = s3.get_object(Bucket=bucket_name, Key=photo_name)
            image_data = img_response['Body'].read()
            
            # CREATE INDEX_ON image_embedding
            img_embedding = get_clip_embedding(image_data)
            create_img_index(img_embedding, photo_name)
                
            # CREATE INDEX_ON text_embedding
            text_embedding = get_clip_text_embedding(data['caption'])
            create_text_index(text_embedding, photo_name)
            
        # print(idx, "completed"+'$'*100)
    return
    
    
    

def lambda_handler(event, context):
    print("Verify the branch work")
    
    # # Already DONE for 250 images!!!
    # print("Generate captions for all the existing images once")
    # response = clip_process_all_images()
    # return response
    print(event)
    # opensearch_indexing_on_all_images()
    # return

    # Triggered when an image is uploaded to the S3 bucket
    try:
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        photo_name = event['Records'][0]['s3']['object']['key']
        # print(bucket_name, photo_name)
        description, tags = s3_caption(photo_name, bucket_name)
        
        print(description, tags)
        s3 = boto3.client('s3')
        if 'jpg' or 'png' in photo_name.lower():
            img_response = s3.get_object(Bucket=bucket_name, Key=photo_name)
            image_data = img_response['Body'].read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # GENERATE CAPTION using sagemaker endpoint
            ml_caption = process_image(base64_image)
            meme = [
                    photo_name.split('.')[0],  
                    "https://memerr-memes.s3.amazonaws.com/"+photo_name,
                    description,
                    "[" + ", ".join(tags) + "]",
                    ml_caption
                ]
            
            metadata_key = photo_name.split('.')[0] + ".json"
            # CREATE INDEX ON image embedding
            img_embedding = get_clip_embedding(image_data)
            create_img_index(img_embedding, photo_name)
            
            # CREATE INDEX_ON text_embedding
            text_embedding = get_clip_text_embedding(ml_caption)
            create_text_index(text_embedding, photo_name)
            
            if description!="":
                text_embedding = get_clip_text_embedding(description)
                create_text_index(text_embedding, photo_name)
                
            # UPLOAD to dynamoDB
            insert_data(meme)
            
        response = "Uploaded captions to DynamoDB successfully"
    except Exception as e:
        print(e)
        response = "Issue with uploading captions to S3 bucket"

    print(response)
    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
