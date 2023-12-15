from functools import wraps
from flask import Flask, jsonify, make_response, request, render_template
from .py.authn import get_jwks, validate_token, sign_in, generate_nonce
import boto3
from .models.profile import UserCreds
import jwt



#region Global Variables
app = Flask(__name__)
# AWS Cognito Configuration
COGNITO_REGION = 'us-east-1'
COGNITO_USER_POOL_ID = 'us-east-1_2xLbaGSV5'
COGNITO_APP_CLIENT_ID = '66oaupmsid03n7ugdbseid111s'
COGNITO_CLIENT = boto3.client('cognito-idp', region_name=COGNITO_REGION)
#endregion



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
def user_page():
    if request.endpoint == "user_signup":
        return render_template("user_signup.html")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=True)
