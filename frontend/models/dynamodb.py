import boto3

class DynamoDB:
    def __init__(self, region_name:str, dynamo_db_table:str):
        # Replace 'your-region' and 'your-dynamodb-table' with your actual AWS region and DynamoDB table name
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.table = self.dynamodb.Table(dynamo_db_table)

    def get_memes_data(self):
        response = self.table.scan()
        memes_data = response.get('Items', [])
        return memes_data