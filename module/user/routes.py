from flask_restful import Resource, reqparse
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import os
import json
from utils.responseUtils import Response  # Assuming ResponseUtil is in response_util.py
from module.user.controller import UsersController  # Assuming UsersController is in users_controller.py
from decimal import Decimal
from utils.commonUtil import authenticate 
# Load configuration
config_path = 'app.json'
with open(config_path, 'r') as config_file:
    config = json.load(config_file)

# Secret key for JWT
SECRET_KEY = config['SECRET_KEY']

# Initialize UsersController
users_controller = UsersController()

class User:
    @staticmethod
    def create_user(email, password, name):
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        response = users_controller.create_user(
            bp_name=name,
            bp_company='',
            bp_industry='',
            bp_email=email,
            bp_password=hashed_password,
            bp_status=1
        )
        return response

    @staticmethod
    def validate_user(email, password):
        response = users_controller.get_users(email=email)
        print(response,"=======================>")
        if response[1] != 200:
            return None
        users = response[0]['data']
        for user in users:
            if user['bp_email'] == email and check_password_hash(user['bp_password'], password):
                return user
        return None

    @staticmethod
    def user_exists(email):
        response = users_controller.get_users()
        if response[1] != 200:
            return False
        users = response[0]['data']
        for user in users:
            if user['bp_email'] == email:
                return True
        return False

class Signup(Resource):
    signup_parser = reqparse.RequestParser()
    signup_parser.add_argument('email', type=str, required=True, help='Email is required')
    signup_parser.add_argument('password', type=str, required=True, help='Password is required')
    signup_parser.add_argument('name', type=str, required=True, help='Name is required')

    def post(self):
        data = self.signup_parser.parse_args()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        
        if User.user_exists(email):
            return Response.bad_request(message='User already exists')
        
        response = User.create_user(email, password, name)
        return response

class Signin(Resource):
    signin_parser = reqparse.RequestParser()
    signin_parser.add_argument('email', type=str, required=True, help='Email is required')
    signin_parser.add_argument('password', type=str, required=True, help='Password is required')

    def post(self):
        data = self.signin_parser.parse_args()
        email = data.get('email')
        password = data.get('password')
        
        user = User.validate_user(email, password)
        print("user========>",user)
        if not user:
            return Response.unauthorized(message='Invalid credentials')
        
        token = jwt.encode({
            'id': user['bp_user_id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, SECRET_KEY, algorithm='HS256')

    
        return Response.success(data={'token': token, 'user': user})

class ForgotPassword(Resource):
    signin_parser = reqparse.RequestParser()
    signin_parser.add_argument('email', type=str, required=True, help='Email is required')

    def post(self):
        data = self.signin_parser.parse_args()
        email = data.get('email')
        
        if not User.user_exists(email):
            return Response.not_found(message='User not found')
        
        # Here you would normally send an email with a reset link or token
        return Response.success(message='Password reset link sent')



class GetUser(Resource):
    
    @authenticate
    def get(self, current_user):
        print("user_id=====>",current_user)
        response = users_controller.get_users(
            id=current_user
        )
        return response

class UpdateUser(Resource):
    update_parser = reqparse.RequestParser()
    update_parser.add_argument('name', type=str, required=False)
    update_parser.add_argument('company', type=str, required=False)
    update_parser.add_argument('industry', type=str, required=False)
    update_parser.add_argument('email', type=str, required=False)
    update_parser.add_argument('password', type=str, required=False)
    update_parser.add_argument('status', type=int, required=False)

    def put(self, user_id):
        data = self.update_parser.parse_args()
        name = data.get('name')
        company = data.get('company')
        industry = data.get('industry')
        email = data.get('email')
        password = data.get('password')
        status = data.get('status')

        if password:
            password = generate_password_hash(password, method='sha256')

        response = users_controller.update_user(
            id=user_id,
            bp_name=name,
            bp_company=company,
            bp_industry=industry,
            bp_email=email,
            bp_password=password,
            bp_status=status
        )

        return response