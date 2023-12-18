import boto3
from boto3.dynamodb.conditions import Key


class DynamoDB:
    def __init__(self, region_name:str, dynamo_db_table:str):
        # Replace 'your-region' and 'your-dynamodb-table' with your actual AWS region and DynamoDB table name
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.table = self.dynamodb.Table(dynamo_db_table)

    def insert_data(self, memes_data):
        if isinstance(memes_data, list):
            for data in memes_data:
                self.table.put_item(Item=data)
        else:
            self.table.put_item(Item=memes_data)

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

