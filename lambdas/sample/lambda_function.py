import os
import logging
import json
import time
import boto3
from botocore.exceptions import ClientError
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth


#region Global Variables
OS_ENV = "America/New_York"
REGION_NAME='us-east-1'
DOMAIN_NAME = 'photos'
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

lambda_client = boto3.client('lambda')
lex_client = boto3.client('lexv2-runtime')
# os_config = Config( region_name=REGION_NAME )
# opensearch_client = boto3.client('opensearch', config=os_config)

# The OpenSearch domain endpoint with https:// and without a trailing slash
os_host = os.getenv('OS_HOST')
credentials = boto3.Session().get_credentials()
os_auth = ('admin', 'admin') # For testing only. Don't store credentials in code.
os_awsauth = AWS4Auth(credentials.access_key, credentials.secret_key,
                REGION_NAME, service="es", session_token=credentials.token)
os_client = OpenSearch(
        hosts=[{'host': os_host, 'port': 443}],
        http_auth=os_awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
#endregion

#region OpenSearch
def search_keyword(query):
    response = os_client.search(index=DOMAIN_NAME, body=query)
    print(f'@search_keyword: {query}; {response}')
    return response

def build_query_single(keyword):
    os_query = {
        "query": {
            "query_string": {
                "default_operator": "OR",
                "default_field": "labels",
                "query": keyword
            }
        }
    }
    return os_query

def build_query_multi(keywords):
    os_query = {
        "size": 5,
        "query": {
            "multi_match": {
                "query": keywords,
                "fields": ["labels", "", "", ""]
            }
        }
    }
    return os_query
#endregion OpenSearch


#region Lex Fx
def call_lex(query):
    session_id = 'test_session'
    response = lex_client.recognize_text(
            botId='LQN6USIYI3',
            botAliasId='J9AMOEOA6G',
            localeId='en_US',
            sessionId=session_id,
            text=query)
    print(f'@call_lex: {query}; {response}')
    return response

def get_slots(lex_response):
    return lex_response["interpretations"][0]["intent"]["slots"]

def get_slot(lex_response, slot_name):
    slots = get_slots(lex_response)
    slot =  slots.get(slot_name, None)
    print('@get_slot: slot', slot)
    return slot

def get_slot_value(value):
    if value['value']:
        slot_values = value['value']
        slot_value = slot_values['resolvedValues'][0].lower() if slot_values['resolvedValues'] else slot_values['interpretedValue'].lower()
        print('@get_slot_value: slot_value', slot_value)
        return slot_value
    else:
        return None
#endregion Lex Fx


def parse_keywords(lex_response):
    print(f'@parse_keywords:INPUT {lex_response}')
    keywords = []
    try:
        if lex_response:
            values = lex_response["interpretations"][0]["intent"]["slots"]["keywords"]["values"]
            for value in values:
                keywords.append(get_slot_value(value))
        return keywords
    except ClientError as ex:
        response = {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            "body":
                {
                    "error": "Failed to parse Lex keywords",
                    "lex_error": str(ex)
                }
        }
        return response

def search_photos(query):
    print(f'@search_photos:INPUT {query}')
    response_from_lex = call_lex(query)
    keywords = parse_keywords(response_from_lex)
    results = []

    try:
        for keyword in keywords:
            query = build_query_single(keyword)
            response_from_os = search_keyword(query)
            items = response_from_os['hits']['hits']
            print(f'items: {items}')
            for item in items:
                aws_bucket = item['_source']['bucket']
                aws_key = item['_source']['objectKey']
                photo_url = f"https://{aws_bucket}.s3.amazonaws.com/{aws_key}"
                photo_item = {
                    'url': photo_url,
                    'labels': item['_source']['labels']
                }
                print(f'photo_item: {photo_item}')
                results.append(photo_item)
        body = { 'results': results }
        print(f'body: {body}')
        response = {
            'headers': {
                'content-type': 'application/json',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'isBase64Encoded': False,
            'statusCode': 200,
            'body': json.dumps(body)
        }
        return response
    except RuntimeError as ex:
        response = {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            "body": { 
                "error": f"Failed at: search_photos for keywords: {keywords}",
                "errorDetail": ex
            }
        }
        return response


'''
TODO: Set up Lambda (nsfw-allowed) to determine whether user can toggle nsfw view based on age
'''


def lambda_handler(event, context):
    print(f'@lambda_handler:INPUT {event}; {context}')
    os.environ['TZ'] = OS_ENV
    time.tzset()
    logger.debug(event)
    query = event["queryStringParameters"]["q"]
    response = search_photos(query)
    return response

'''
TODO:
- Create a Lex bot to handle search-photos queries by keywords
- Get the keywords from Lex (multi-valued-slots), then parse it
- Search for photo item with OpenSearch with OS query
- Return the photos from the keywords
- Must handle for singular and plural keyword queries; 2+ keywords per query

References
- https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless-sdk.html
- https://docs.aws.amazon.com/opensearch-service/latest/developerguide/search-example.html
- https://docs.aws.amazon.com/opensearch-service/latest/developerguide/configuration-samples.html#configuration-samples-python
- https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/opensearch.html
- https://docs.aws.amazon.com/opensearch-service/latest/developerguide/what-is.html
- https://opensearch.org/docs/latest/query-dsl/full-text/query-string/
- https://docs.aws.amazon.com/lexv2/latest/dg/multi-valued-slots.html
'''