import boto3
import json
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch
from elasticsearch import RequestsHttpConnection
import ast


index_name = "memerrsearch"
opensearch_url = "search-memerrsearch-hbgsqydnohjzfv26vjj4h3wi44.us-east-1.es.amazonaws.com"
opensearch_region = "us-east-1"


def search_products_text(es, embedding, k = 10):
    index_name = "textsearch"
    body = {
        "size": k,
        "_source": {
            "exclude": ["embeddings"],
        },
        "query": {
            "knn": {
                "embeddings": {
                    "vector": embedding,
                    "k": k,
                }
            }
        },
    }        
    res = es.search(index=index_name, body=body)
    images = []
    for hit in res["hits"]["hits"]:
        id_ = hit["_id"]
        # image, item_name = get_image_from_item_id(id_)
        # image.name_and_score = f'{hit["_score"]}:{item_name}'
        images.append(id_)
    return images
    
def search_products(es, embedding, k = 10):
    body = {
        "size": k,
        "_source": {
            "exclude": ["embeddings"],
        },
        "query": {
            "knn": {
                "embeddings": {
                    "vector": embedding,
                    "k": k,
                }
            }
        },
    }        
    res = es.search(index=index_name, body=body)
    images = []
    for hit in res["hits"]["hits"]:
        id_ = hit["_id"]
        # image, item_name = get_image_from_item_id(id_)
        # image.name_and_score = f'{hit["_score"]}:{item_name}'
        images.append(id_)
    return images


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


def get_clip_embedding(query_text):
    input_data = {"inputs": query_text}
    runtime= boto3.client('runtime.sagemaker')

    response = runtime.invoke_endpoint(EndpointName="clip-text-model-2023-12-16-05-20-21-704",
                                       ContentType='application/json',
                                       Body=json.dumps(input_data))
    
    result = str(response['Body'].read())
    emb = json.loads(eval(result))[0]
    return emb


def lambda_handler(event, context):
    
    # You can check if the index is created within your es cluster
    es = get_es_client()
    print(es.indices.get_alias("*"))
    
    query_text = event["queryStringParameters"]['q']
    print(query_text)
    embedding = get_clip_embedding(query_text)
    print("embeddings received ", embedding)
    
    img_paths = search_products(es,embedding)
    img_paths_text_to_txt = search_products_text(es,embedding)
    for item in img_paths_text_to_txt:
        img_paths.append(item)
        
    img_paths = list(set(img_paths))
        
    print(img_paths)
    
    return{
            'statusCode': 200,
            'headers': {"Access-Control-Allow-Origin":"*"},
            'body': json.dumps({
                'imagePaths':img_paths,
                'userQuery':query_text,
            }),
            'isBase64Encoded': False
        }
