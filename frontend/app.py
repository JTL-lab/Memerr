from functools import wraps
import urllib
import requests
import boto3
from flask import Flask, jsonify, make_response, request, render_template, redirect
from flask_cors import CORS
import jwt
from .models.profile import UserCreds
from .py.authn import get_jwks, validate_token, sign_in, generate_nonce



#region Global Variables
app = Flask(__name__)
CORS(app)
# AWS Cognito Configuration
COGNITO_REGION = 'us-east-1'
COGNITO_USER_POOL_ID = 'us-east-1_2xLbaGSV5'
COGNITO_DOMAIN = 'memerr.auth.us-east-1.amazoncognito.com'
FRONTEND_DOMAIN = 'https://ec2-54-83-82-72.compute-1.amazonaws.com'
COGNITO_CLIENT = boto3.client('cognito-idp', region_name=COGNITO_REGION)
SCOPES = 'openid profile email'
TOKEN_ENDPOINT = f"https://{COGNITO_DOMAIN}/oauth2/token"
COGNITO_APP_CLIENT_ID = '4h26gjmvon4b6befhs9vsv83p2'
COGNITO_APP_CLIENT_SECRET = 'oa6kd698oo3d97sj8q4rtmtskl4809l7kl9atbdjcjb2eududmb'
REDIRECT_URI = 'https://ec2-54-83-82-72.compute-1.amazonaws.com/callback'
COGNITO_LOGIN_URL_HARDCODED = f'https://{FRONTEND_DOMAIN}/login?response_type=code&client_id={COGNITO_APP_CLIENT_ID}&redirect_uri={REDIRECT_URI}'
#endregion



# Token Validation Decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        access_token = None
        if 'Authorization' in request.headers:
            access_token = request.headers.get('Authorization')
        if not access_token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            jwks = get_jwks()
            print(jwks)
            user = validate_token(access_token)
            if user is None:
                return jsonify({'message': 'Unauthorized'}), 401
        except Exception as e:
            return jsonify({'message': f'Token is invalid! Error {e}'}), 401

        return f(*args, **kwargs)
    return decorated


# User Registration
@app.route('/register', methods=['POST'])
def register():
    # Implement /register
    return jsonify({'message': 'User created successfully'}), 201

# User Login
@app.route('/login-with-creds', methods=['POST'])
def login_with_creds():
    # Implement /login
    content = request.json
    username = content.get('username')
    password = content.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    user_creds = UserCreds(username, password)
    print(f'user_creds: {user_creds}')
    id_token = sign_in(user_creds)
    if id_token:
        # Create a response object and set the JWT token in a cookie
        response = make_response(jsonify({"message": "Login successful"}))
        response.set_cookie('token', id_token, httponly=True, secure=True)
        return jsonify({'message': 'Login successful', 'idToken': id_token})
    else:
        return jsonify({'message': 'Login failed'}), 401

# User Login
@app.route('/login', methods=['GET'])
def login():
    login_query_params = {
        "response_type": "code",
        "client_id": COGNITO_APP_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        # "scope": SCOPES,
    }
    cognito_login_url = f"https://{COGNITO_DOMAIN}/login?{urllib.parse.urlencode(login_query_params)}"
    print(f'@login cognito_login_url {cognito_login_url}')
    return redirect(cognito_login_url)
    # nonce = generate_nonce()
    # response = make_response(render_template(COGNITO_LOGIN_URL, nonce=nonce))
    # response.headers['Content-Security-Policy'] = f"script-src 'nonce-{nonce}'"
    # return response

@app.route('/callback')
def callback():
    # Exchange the authV code for tokens (ID, access, refresh) using the Cognito Token endpoint
    try:
        print('@callback Start')
        code = request.args.get('code')
        print(f'@callback code: {code}')

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'authorization_code',
            'client_id': COGNITO_APP_CLIENT_ID,
            'client_secret': COGNITO_APP_CLIENT_SECRET,
            'code': code,
            'redirect_uri': REDIRECT_URI
        }
        print(f'@callback data: {data}')
        response = requests.post(TOKEN_ENDPOINT, headers=headers, data=data, timeout=5000)
        print(f'@callback response: {response}')

        if response.status_code == 200:
            tokens = response.json()
            print(f'@callback authV code: {tokens}')
            return tokens
        else:
            return 'Error exchanging code for tokens', response.status_code
    except Exception as e:
        return jsonify({'message': f'Callback Failed! Error {e}, code {code}, data {data}, response {response}'}), 401

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


# Protected Route: Logout
@app.route('/logout')
@token_required
def logout():
    # Implement /logout
    response = make_response(jsonify({"message": "Logout successful"}))
    response.set_cookie('token', '', expires=0)
    return response


@app.errorhandler(404)
def error(err):
    return 'oops, nothing here', 404


@app.route("/")
def index():
    nonce = generate_nonce()
    response = make_response(render_template("index.html", nonce=nonce))
    response.headers['Content-Security-Policy'] = f"script-src 'nonce-{nonce}'"
    return response


@app.route("/user/create", endpoint="user_signup", methods=["GET"])
def user_signup_page():
    if request.endpoint == "user_signup":
        return render_template("user_signup.html")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=True, ssl_context='adhoc')
