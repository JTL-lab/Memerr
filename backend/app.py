#!/usr/bin/python3
from flask import Flask, request, jsonify
import boto3
import jwt
from functools import wraps
from authn import get_jwks, validate_token, authn_handler, sign_in
import os
import requests


app = Flask(__name__)
# AWS Cognito Configuration
COGNITO_REGION = 'us-east-1'
COGNITO_USER_POOL_ID = 'us-east-1_2xLbaGSV5'
COGNITO_APP_CLIENT_ID = '66oaupmsid03n7ugdbseid111s'
COGNITO_CLIENT = boto3.client('cognito-idp', region_name=COGNITO_REGION)
# Add your function definitions here (e.g., sign_in, validate_token)

# Token Validation Decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            jwks = get_jwks()
            print(jwks)
            user = validate_token(token)
            if user is None:
                return jsonify({'message': 'Unauthorized'}), 401
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(*args, **kwargs)

    return decorated

# User Registration
@app.route('/register', methods=['POST'])
def register():
    # Implement /register
    return jsonify({'message': 'User created successfully'}), 201

# User Login
@app.route('/login', methods=['POST'])
def login():
    # Implement /login
    content = request.json
    username = content.get('username')
    password = content.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    id_token = sign_in(username, password)
    if id_token:
        return jsonify({'message': 'Login successful', 'idToken': id_token})
    else:
        return jsonify({'message': 'Login failed'}), 401

# Protected Route: Share a Meme
@app.route('/share-meme', methods=['POST'])
@token_required
def share_meme():
    # token = request.headers.get('Authorization')
    # user = validate_token(token)
    # if user is None:
    #     return jsonify({'message': 'Unauthorized'}), 401

    # Implement /share-meme
    return jsonify({'message': '/share-meme success!'})

# Protected Route: Rate a Meme
@app.route('/rate-meme', methods=['POST'])
@token_required
def rate_meme():
    # token = request.headers.get('Authorization')
    # user = validate_token(token)
    # if user is None:
    #     return jsonify({'message': 'Unauthorized'}), 401

    # Implement /rate-meme
    return jsonify({'message': '/rate-meme success!'})


@app.errorhandler(404)
def error(err):
    return 'oops, nothing here', 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, threaded=True)
    # app.run(debug=True)
