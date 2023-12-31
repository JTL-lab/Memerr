from functools import wraps
import urllib
import logging
import ast
import requests
import boto3
import redis
import time
from flask import Flask, jsonify, make_response, request, render_template, redirect, current_app
from flask_cors import CORS
import jwt
from frontend.models.profile import UserCreds
from frontend.py.authn import get_jwks, validate_token, create_redis_client
from frontend.models.dynamodb import DynamoDB as DynamoDBHelper
import random
import string
import json

#region Global Variables
app = Flask(__name__)
CORS(app)
handler = logging.FileHandler('app.log')  # Ouput: app.log
handler.setLevel(logging.INFO)  # Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
app.logger.addHandler(handler)
# AWS Cognito Configuration
COGNITO_REGION = 'us-east-1'
COGNITO_USER_POOL_ID = 'us-east-1_2xLbaGSV5'
COGNITO_DOMAIN = 'memerr.auth.us-east-1.amazoncognito.com'
FRONTEND_DOMAIN = 'ec2-54-86-68-35.compute-1.amazonaws.com'
# FRONTEND_DOMAIN = 'localhost:5001'
COGNITO_CLIENT = boto3.client('cognito-idp', region_name=COGNITO_REGION)
SCOPES = 'openid profile email'
TOKEN_ENDPOINT = f"https://{COGNITO_DOMAIN}/oauth2/token"
COGNITO_APP_CLIENT_ID = '4h26gjmvon4b6befhs9vsv83p2'
COGNITO_APP_CLIENT_SECRET = 'oa6kd698oo3d97sj8q4rtmtskl4809l7kl9atbdjcjb2eududmb'
REDIRECT_URI = f'http://{FRONTEND_DOMAIN}/callback'
COGNITO_LOGIN_URL_HARDCODED = f'https://{FRONTEND_DOMAIN}/login?response_type=code&client_id={COGNITO_APP_CLIENT_ID}&redirect_uri={REDIRECT_URI}'

# Initialize Redis
# Configure Redis connection
redis_host = "memerr-dqyhmc.serverless.use1.cache.amazonaws.com"
redis_port = 6379
redis_client = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

REGION = 'us-east-1'
BUCKET_DOMAIN = 'https://memerr-memes.s3.amazonaws.com/'
dynamodb_resource = boto3.resource('dynamodb', region_name=REGION)

old_meme_table = DynamoDBHelper(REGION, "meme-data")
meme_table = DynamoDBHelper(REGION, "meme-data-new")
user_table = DynamoDBHelper(REGION, "user-info")

USER_EMAIL = "uttam.gurram99@gmail.com"
csp_policy = "script-src https://d3oia8etllorh5.cloudfront.net https://memerr.auth.us-east-1.amazoncognito.com 'unsafe-inline';"

#endregion


#region AWS Redis Elasticache
"""
# Set a multi-value object on Redis cache
user_data = {
    'access_token': 'access_token_value',
    'id_token': 'id_token_value',
    'email': 'memerr6698@gmail.com',
    'profilepicurl': 'https://lh3.googleusercontent.com/a/ACg8ocLhdNuuMKRGaK4BP2MizRLfPG-fNV7t89WH-srUYkI0Aw=s96-c'
}
set_user_data('memerr6698@gmail.com', user_data)

# Get a multi-value object, data on Redis cache
data = get_user_data('memerr6698@gmail.com')
if data:
    access_token = data.get('access_token')
    email = data.get('email')
"""

# redis_client = create_redis_client('memerr-dqyhmc.serverless.use1.cache.amazonaws.com', 6379)
@app.after_request
def add_csp_header(response):
    response.headers['Content-Security-Policy'] = csp_policy
    return response


def generate_unique_key(file_name):
    # Generate a timestamp string
    timestamp = int(time.time())

    # Generate a random string
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=13))

    # Combine both with an underscore separator
    unique_key = f"{timestamp}_{random_string}_"

    # Append the original filename
    unique_key += file_name

    return unique_key


# Set multiple values in Redis using a hash
def set_user_data(user_id, user_data, expiration=3600):
    try:
        # Serialize the user data as JSON
        user_data_json = json.dumps(user_data)
        
        # Set the serialized JSON in Redis with an expiration time
        redis_client.setex(f"user_data:{user_id}", expiration, user_data_json)
        return True
    except Exception as e:
        app.logger.error(f"Failed to set user data in Redis: {e}")
        return False

# Get multiple values from Redis
def get_user_data(user_id):
    try:
        # Get the serialized JSON from Redis
        user_data_json = redis_client.get(f"user_data:{user_id}")
        
        if user_data_json is not None:
            # Deserialize the JSON and return the user data as a dictionary
            return json.loads(user_data_json)
        else:
            return None
    except Exception as e:
        app.logger.error(f"Failed to get user data from Redis: {e}")
        return None
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
            app.logger.info(jwks)
            user = validate_token(access_token)
            if user is None:
                return jsonify({'message': 'Unauthorized'}), 401
        except Exception as e:
            return jsonify({'message': f'Token is invalid! Error {e}'}), 401

        return f(*args, **kwargs)
    return decorated


# User Upload
@app.route('/upload', methods=['POST'])
def upload_image():

    UPLOAD_API_ENDPOINT = "https://1n88dyemv5.execute-api.us-east-1.amazonaws.com/memesearch/upload/memerr-memes"
    try:
        title = request.form.get('title')
        description = request.form.get('description')
        tags = request.form.get('tags')
        image = request.files['image']
        tags = [tag for tag in tags.split(',')]


        # Ensure the file is present
        if not image:
            return jsonify({'error': 'No file provided'}), 400

        # Construct the file path
        file_ext = ".png"
        file_name = generate_unique_key(file_ext)
        print(file_name)
        # Prepare headers for the S3 upload
        headers = {
            "x-amz-meta-customLabels": json.dumps({
                
                "description" : description,
                "tags" : tags,

                }),
            'content-type': "image/png"
        }

        # Make an HTTP PUT request to the upload endpoint with the file and custom labels as parameters
        response = requests.put(
            f"{UPLOAD_API_ENDPOINT}/{file_name}",
            headers=headers,
            data = image.read()
        )
        
        if response.status_code == 200:
            return jsonify({'message': 'File uploaded successfully'})
        else:
            return jsonify({'error': 'Failed to upload file to S3'}), 500

    except Exception as e:
        print("Error handling upload:", str(e))
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/search', methods=['GET'])
def get_image_paths():
    nonce = "nonce"
    SEARCH_API_ENDPOINT = "https://1n88dyemv5.execute-api.us-east-1.amazonaws.com/memesearch/search"
    app.logger.info(SEARCH_API_ENDPOINT)
    try:
        # You can customize the query parameters based on your API
        query_parameters = {'q': request.args.get("query")}

        # Make a GET request to the search API endpoint
        response = requests.get(SEARCH_API_ENDPOINT, params=query_parameters)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            api_data = response.json()
            image_paths = api_data.get('imagePaths', [])
            user_query = api_data.get('userQuery', '')
            img_paths = ["https://memerr-memes.s3.amazonaws.com/"+item for item in image_paths]

            memes_data = old_meme_table.retrieve_memes(image_paths, "meme_id")
    
            for data in memes_data:
                # data['categories'] = json.loads(data['categories'])
                categories_str = data['categories'].strip("[]")
                tag_list = [tag.strip() for tag in categories_str.split(',')]
                data['categories'] = tag_list
            
            print(memes_data)
            response = make_response(render_template("index.html", nonce=nonce, memes_data=memes_data))
            return response

            return jsonify({'image_paths': img_paths})
        else:
            # If the API request was not successful, handle the error
            return jsonify({'error': f'Error from API: {response.status_code}'})

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'})

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
    app.logger.info(f'@login cognito_login_url {cognito_login_url}')
    return redirect(cognito_login_url)
    # nonce = generate_nonce()
    # response = make_response(render_template(COGNITO_LOGIN_URL, nonce=nonce))
    # response.headers['Content-Security-Policy'] = f"script-src 'nonce-{nonce}'"
    # return response

@app.route('/callback')
def callback():
    # Exchange the authV code for tokens (ID, access, refresh) using the Cognito Token endpoint
    try:
        app.logger.info('@callback Start')
        code = request.args.get('code')
        app.logger.info(f'@callback code: {code}')

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
        app.logger.info(f'@callback data: {data}')
        response = requests.post(TOKEN_ENDPOINT, headers=headers, data=data, timeout=5000)
        app.logger.info(f'@callback response: {response}')

        if response.status_code == 200:
            tokens = response.json()
            app.logger.info(f'@callback authV tokens: {tokens}')

            # access_token
            access_token = tokens.get('access_token')
            app.logger.info(f'@callback access_token: {access_token}')
            print(f'access_token {access_token}')

            # id_token
            id_token = tokens.get('id_token')
            app.logger.info(f'@callback id_token: {id_token}')
            print(f'id_token {id_token}')
            payload = validate_token(id_token)

            # email
            email = payload.get('email')
            app.logger.info(f'@callback email: {email}')
            print(f'email {email}')

            # profile picture url
            picture = payload.get('picture')
            app.logger.info(f'@callback picture: {picture}')
            print(f'profile_picture_url {picture}')

            # Set a multi-value object on Redis cache
            user_data = {
                'access_token': access_token,
                'id_token': id_token,
                'email': email,
                'picture': picture
            }
            # TODO: USE THEM ONCE LOGIN WORKS
            # global USER_EMAIL
            # USER_EMAIL = user_data['email']

            # global USER_PICTURE
            # USER_PICTURE = user_data['picture'] 

            # set_user_data(email, user_data)
            print(f'set_user_data: {user_data}')
            app.logger.info(f'@set_user_data: {user_data}')

            # Get a multi-value object, data on Redis cache
            # data = get_user_data(email)
            app.logger.info(f'@get_user_data: {data}')
            print(f'get_user_data: {data}')
            # if data:
            #     access_token = data.get('access_token')
            #     email = data.get('email')

            index_url = f"http://{FRONTEND_DOMAIN}/"
            app.logger.info(f'@login FRONTEND_DOMAIN {index_url}')
            return redirect(index_url)
            # return data
        else:
            return 'Error exchanging code for tokens', response.status_code
    except Exception as e:
        return jsonify({'message': f'Callback Failed! Error {e}, code {code}, data {data}, response {response}'}), 401

# Protected Route: Save a meme
@app.route('/save-meme', methods=['POST'])
# @token_required
def save_meme():
    # token = request.headers.get('Authorization')
    # user = validate_token(token)
    # if user is None:
    #     return jsonify({'message': 'Unauthorized'}), 401

    # Implement /share-meme
    global USER_EMAIL

    try:
        memeId = request.form.get('memeId')
        email_ids = [str(USER_EMAIL)]
        user_data = user_table.retrieve_memes(email_ids, "email")[0]

        user_saved_memes = ast.literal_eval(user_data['memes_saved'])
        # save a meme if not present else remove if already present
        if str(memeId) not in user_saved_memes:
            user_saved_memes.append(str(memeId))
        else:
            user_saved_memes.remove(str(memeId))

        user_data['memes_saved'] = str(user_saved_memes)
        user_table.insert_data(user_data)
    except:
        jsonify({'message': '/save-meme failure!'})

    return jsonify({'message': '/save-meme success!'})

# Protected Route: Rate a Meme
@app.route('/rate-meme', methods=['POST'])
# @token_required
def rate_meme():
    # token = request.headers.get('Authorization')
    # user = validate_token(token)
    # if user is None:
    #     return jsonify({'message': 'Unauthorized'}), 401

    # Implement /rate-meme
    global USER_EMAIL

    try:
        memeId = request.form.get('memeId')
        humorRating = request.form.get('humorRating')
        originalityRating = request.form.get('originalityRating')
        reliabilityRating = request.form.get('reliabilityRating')
        print(memeId, humorRating, originalityRating, reliabilityRating)

        meme_ids = [str(memeId)]

        # Get the item from DynamoDB
        memes_data = meme_table.retrieve_memes(meme_ids, "meme_id")[0]
        new_relatability_rating = float(memes_data['relatability_rating']) * float(memes_data['num_ratings']) + float(reliabilityRating)
        new_originality_rating = float(memes_data['originality_rating']) * float(memes_data['num_ratings']) + float(originalityRating) 
        new_humor_rating = float(memes_data['humor_rating']) * float(memes_data['num_ratings']) + float(humorRating)

        new_num_ratings =  int(memes_data['num_ratings']) + 1

        new_relatability_rating /= new_num_ratings
        new_originality_rating /= new_num_ratings
        new_humor_rating /= new_num_ratings

        memes_data['relatability_rating'] = str(round(new_relatability_rating, 2))
        memes_data['originality_rating'] = str(round(new_originality_rating,2))
        memes_data['humor_rating'] = str(round(new_humor_rating,2))
        memes_data['num_ratings'] = str(new_num_ratings)

        meme_table.insert_data(memes_data)

        email_ids = [str(USER_EMAIL)]
        user_data = user_table.retrieve_memes(email_ids, "email")[0]

        user_rated_memes = json.loads(user_data['memes_rated'].replace("'", "\""))
        user_rated_memes[str(memeId)] = {'humor_rating': str(humorRating), 'originality_rating': str(originalityRating), 'relatability_rating': str(reliabilityRating)}
        user_data['memes_rated'] = str(user_rated_memes)

        user_table.insert_data(user_data)
    except:
        return jsonify({'message': '/rate-meme failure!'})
    
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
    # nonce = generate_nonce()
    nonce = "nonce"
    memes_data = meme_table.get_memes_data()[0:100]
    for data in memes_data:
        # data['categories'] = json.loads(data['categories'])
        categories_str = data['categories'].replace("[", "")
        categories_str = categories_str.replace("]", "")
        categories_str = categories_str.replace('"', "")
        tag_list = [tag.strip() for tag in categories_str.split(',')]
        data['categories'] = tag_list
        data['description'] = data['caption']
        data['caption'] = data['ml_caption']

    response = make_response(render_template("index.html", nonce=nonce, memes_data=memes_data))
    # response.headers['Content-Security-Policy'] = f"script-src 'nonce-{nonce}'"
    return response

@app.route("/recommend")
def get_relevant_memes():
    nonce = "nonce"#generate_nonce()
    user_data = user_table.query_single(query_id=USER_EMAIL, primary_key="email")[0]
    meme_ids = list(ast.literal_eval(user_data['memes_saved']))
    RECOMMEND_API_ENDPOINT = "https://1n88dyemv5.execute-api.us-east-1.amazonaws.com/memesearch/recommend"
    app.logger.info(RECOMMEND_API_ENDPOINT)
    try:
        # You can customize the query parameters based on your API
        query_parameters = {'q': ",".join(item for item in meme_ids)}

        # Make a GET request to the search API endpoint
        response = requests.get(RECOMMEND_API_ENDPOINT, params=query_parameters)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            api_data = response.json()
            image_paths = api_data.get('imagePaths', [])
            img_paths = ["https://memerr-memes.s3.amazonaws.com/"+item for item in image_paths]
            print(img_paths)
            memes_data = old_meme_table.retrieve_memes(image_paths, "meme_id")
            
            for data in memes_data:
                # data['categories'] = json.loads(data['categories'])
                categories_str = data['categories'].replace("[", "")
                categories_str = categories_str.replace("]", "")
                categories_str = categories_str.replace('"', "")
                tag_list = [tag.strip() for tag in categories_str.split(',')]
                data['categories'] = tag_list
                data['description'] = data['caption']
                data['caption'] = "ml_caption"
        
            return render_template("user_saved.html", nonce=nonce, memes_data=memes_data) 
            # response = make_response(render_template("index.html", nonce=nonce, memes_data=memes_data))
            # return response

            # return jsonify({'image_paths': img_paths})
        else:
            # If the API request was not successful, handle the error
            return jsonify({'error': f'Error from API: {response.status_code}'})

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'})




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
    app.logger.info(f'user_creds: {user_creds}')
    id_token = sign_in(user_creds)
    if id_token:
        # Create a response object and set the JWT token in a cookie
        response = make_response(jsonify({"message": "Login successful"}))
        response.set_cookie('token', id_token, httponly=True, secure=True)
        return jsonify({'message': 'Login successful', 'idToken': id_token})
    else:
        return jsonify({'message': 'Login failed'}), 401


@app.route("/user/create", endpoint="user_signup", methods=["GET"])
def user_signup_page():
    if request.endpoint == "user_signup":
        return render_template("user_signup.html")

# redirect from home to user profile and show the user-rated memes from the user-info Dynamo DB table
@app.route("/user", endpoint="user_profile", methods=["GET"])
def user_profile_page():
    if request.endpoint == "user_profile":
        nonce = "nonce"
        user_data = user_table.query_single(query_id=USER_EMAIL, primary_key="email")[0]
        meme_ids = list(ast.literal_eval(user_data['memes_rated']).keys())
        memes_data = meme_table.retrieve_memes(meme_ids, "meme_id")
        
        for data in memes_data:
            # data['categories'] = json.loads(data['categories'])
            categories_str = data['categories'].replace("[", "")
            categories_str = categories_str.replace("]", "")
            categories_str = categories_str.replace('"', "")
            tag_list = [tag.strip() for tag in categories_str.split(',')]
            data['categories'] = tag_list
            data['description'] = data['caption']
            data['caption'] = data['ml_caption']
        
        return render_template("user.html", nonce=nonce, memes_data=memes_data) 
    else:
        return jsonify({'ok': False, 'message': 'Profile not available'})

# fetch the user posted memes from the user-info Dynamo DB table
@app.route("/user/posted", endpoint="user_posted", methods=["GET"])
def user_posted_page():
    if request.endpoint == "user_posted":
        nonce = "nonce"
        user_data = user_table.query_single(query_id=USER_EMAIL, primary_key="email")[0]
        meme_ids = list(ast.literal_eval(user_data['memes_posted']))
        memes_data = meme_table.retrieve_memes(meme_ids, "meme_id")
        
        for data in memes_data:
            # data['categories'] = json.loads(data['categories'])
            categories_str = data['categories'].replace("[", "")
            categories_str = categories_str.replace("]", "")
            categories_str = categories_str.replace('"', "")
            tag_list = [tag.strip() for tag in categories_str.split(',')]
            data['categories'] = tag_list
            data['description'] = data['caption']
            data['caption'] = data['ml_caption']

        return render_template("user_posted.html", nonce=nonce, memes_data=memes_data) 
    else:
        return jsonify({'ok': False, 'message': 'Profile not available'})
    


# fetch the user saved memes from the user-info Dynamo DB table
@app.route("/user/saved", endpoint="user_saved", methods=["GET"])
def user_saved_page():
    if request.endpoint == "user_saved":
        nonce = "nonce"
        user_data = user_table.query_single(query_id=USER_EMAIL, primary_key="email")[0]
        meme_ids = list(ast.literal_eval(user_data['memes_saved']))
        memes_data = meme_table.retrieve_memes(meme_ids, "meme_id")
        
        for data in memes_data:
            # data['categories'] = json.loads(data['categories'])
            categories_str = data['categories'].replace("[", "")
            categories_str = categories_str.replace("]", "")
            categories_str = categories_str.replace('"', "")
            tag_list = [tag.strip() for tag in categories_str.split(',')]
            data['categories'] = tag_list
            data['description'] = data['caption']
            data['caption'] = data['ml_caption']
        
        return render_template("user_saved.html", nonce=nonce, memes_data=memes_data)  
    else:
        return jsonify({'ok': False, 'message': 'Profile not available'})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=True, ssl_context='adhoc')
