import logging
import os
import requests
from botocore.exceptions import ClientError
import boto3
import jwt

COGNITO_REGION = 'us-east-1'
COGNITO_APP_CLIENT_ID = '66oaupmsid03n7ugdbseid111s'
COGNITO_USER_POOL_ID = 'us-east-1_2xLbaGSV5'
JWKS_URL = 'https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json'
COGNITO_ISSUER = 'https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}'

client = boto3.client('cognito-idp', region_name=COGNITO_REGION)
# dynamodb = boto3.resource('dynamodb', region_name=COGNITO_REGION)
# table_user = dynamodb.Table('')

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def get_jwks():
    response = requests.get(JWKS_URL, timeout=20)
    return response.json()

def validate_token(token):
    try:
        # Decode the JWT header
        headers = jwt.get_unverified_header(token)

        jwks = get_jwks()
        print(jwks)
        headers = jwt.get_unverified_header(token)

        # Find the key from JWKS
        key = next((key for key in jwks['keys'] if key['kid'] == headers['kid']), None)
        if not key:
            raise ValueError('Key not found in JWKS')

        # Construct the public key
        public_key = jwt.RSAAlgorithm.from_jwk(key)

        # Decode and validate the JWT
        payload = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=COGNITO_APP_CLIENT_ID,
            issuer=COGNITO_ISSUER
        )
        return payload
    except jwt.ExpiredSignatureError as e:
        raise ValueError('Token is expired') from e
    except jwt.InvalidTokenError as e:
        raise ValueError('Invalid token') from e
    except Exception as e:
        # General error (i.e. network issues)
        raise ValueError(f'Error validating the token: {str(e)}') from e

def authn_handler(user_creds):
    print(f'@authn_handler: {user_creds}')
    username = user_creds.get('username')
    password = user_creds.get('password')

    if not username or not password:
        print("Username or password missing")
        return None

    token = sign_in(user_creds)
    print(token)

    payload = validate_token(token)
    print(payload)


def sign_up(user_creds):
    try:
        print(f'@sign_up: {user_creds}')
        username = user_creds.get('username')
        password = user_creds.get('password')
        email = user_creds.get('email')

        if not username or not password or not email:
            print("Error: sign_up Failed; Missing fields!")
            return None

        response = client.sign_up(
            ClientId=COGNITO_APP_CLIENT_ID,
            Username=username,
            Password=password,
            UserAttributes=[{'Name': 'email', 'Value': email}]
        )
        print(response)
        return response
    except client.exceptions.UsernameExistsException:
        # Handle exception for duplicate username
        pass
    except Exception as e:
        # General error
        # print(e)
        pass


def sign_in(user_creds):
    try:
        print(f'@sign_in: {user_creds}')
        username = user_creds.get('username')
        password = user_creds.get('password')

        if not username or not password:
            print("Error: sign_in Failed; Username or password missing!")
            return None

        response = client.initiate_auth(
            ClientId=COGNITO_APP_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={'USERNAME': username, 'PASSWORD': password}
        )
        print(response)
        return response['AuthenticationResult']['IdToken']
    except ClientError as e:
        # Handle Cognito client errors (i.e. user not found, wrong password)
        raise ValueError(f'Sign-in error: {e.response["Error"]["Message"]}') from e
    except Exception as e:
        # General error
        print(f"Sign-in error: {str(e)}")
        raise ValueError(f'An error occurred during sign-in: {str(e)}') from e


def get_aws_credentials(google_token, identity_pool_id, region='us-east-1'):
    aws_cognito_identity_client = boto3.client('cognito-identity', region_name=region)

    response = aws_cognito_identity_client.get_id(
        IdentityPoolId=identity_pool_id,
        Logins={
            'accounts.google.com': google_token
        }
    )

    identity_id = response['IdentityId']

    response = client.get_credentials_for_identity(
        IdentityId=identity_id,
        Logins={
            'accounts.google.com': google_token
        }
    )

    return response['Credentials']


def generate_nonce():
    return os.urandom(16).hex()
