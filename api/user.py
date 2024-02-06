import json, jwt
from flask import Blueprint, request, jsonify, current_app, Response
from flask_restful import Api, Resource # used for REST API building
from datetime import datetime
from auth_middleware import token_required

from model.users import User, Design

user_api = Blueprint('user_api', __name__,
                   url_prefix='/api/users')

# API docs https://flask-restful.readthedocs.io/en/latest/api.html
api = Api(user_api)

class UserAPI:        
    class _CRUD(Resource):  # User API operation for Create, Read.  THe Update, Delete methods need to be implemeented
        def post(self): # Create method
            ''' Read data for json body '''
            body = request.get_json()
            
            ''' Avoid garbage in, error checking '''
            # validate name
            name = body.get('name')
            if name is None or len(name) < 2:
                return {'message': f'Name is missing, or is less than 2 characters'}, 400
            # validate uid
            uid = body.get('uid')
            if uid is None or len(uid) < 2:
                return {'message': f'User ID is missing, or is less than 2 characters'}, 400
            # look for password and dob
            password = body.get('password')
            dob = body.get('dob')

            ''' #1: Key code block, setup USER OBJECT '''
            uo = User(name=name, 
                      uid=uid)
            
            ''' Additional garbage error checking '''
            # set password if provided
            if password is not None:
                uo.set_password(password)
            # convert to date type
            if dob is not None:
                try:
                    uo.dob = datetime.strptime(dob, '%Y-%m-%d').date()
                except:
                    return {'message': f'Date of birth format error {dob}, must be mm-dd-yyyy'}, 400
            
            ''' #2: Key Code block to add user to database '''
            # create user in database
            user = uo.create()
            print(uo)
            # success returns json of user
            if user:
                return jsonify(user.read())
            # failure returns error
            return {'message': f'Processed {name}, either a format error or User ID {uid} is duplicate'}, 400

        @token_required
        def get(self, current_user): # Read Method
            print("get successful")
            users = User.query.all()    # read/extract all users from database
            json_ready = [user.read() for user in users]  # prepare output in json
            return jsonify(json_ready)  # jsonify creates Flask response object, more specific to APIs than json.dumps
        
        @token_required
        def put(self, current_user):
            body = request.get_json() # get the body of the request
            token = request.cookies.get("jwt")
            cur_user = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])['_uid']
            uid = body.get('uid')
            name = body.get('name')
            password = body.get('password')
            users = User.query.all()
            for user in users:
                if user.uid == cur_user:
                    user.update(name,uid,password)
            return f"{user.read()} Updated"
        
        @token_required
        def delete(self, current_user):
        # body = request.get_json()
            token = request.cookies.get("jwt")
            cur_user = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])['_uid']
            users = User.query.all()
            for user in users:
                if user.uid==cur_user: # modified with the and user.id==cur_user so random users can't delete other ppl
                    user.delete()
            return jsonify(user.read())
    
    class _DesignCRUD(Resource):  # Design CRUD
        @token_required
        def post(self, current_user): # Create design
            ''' Read data for json body '''
            token = request.cookies.get("jwt")
            cur_user = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])['_uid']
            users = User.query.all()
            for user in users:
                if user.uid==cur_user: # modified with the and user.id==cur_user so random users can't delete other ppl
                    id = user.id
                    owner = user
            body = request.get_json()
            name = body.get('name')
            content = body.get('content')
            type = body.get('type')
            if (type != "public" and type != "private"):
                return {'message': f'Design type must be public or private'}, 400
            do = Design(id=id, type=type, content=content, name=name)
            design = do.create()
            # success returns json of user
            if design:
                return jsonify(user.read())
        
        @token_required
        def put(self, current_user):
            body = request.get_json() # get the body of the request
            token = request.cookies.get("jwt")
            cur_user = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])['_uid']
            users = User.query.all()
            for user in users:
                if user.uid==cur_user: # modified with the and user.id==cur_user so random users can't delete other ppl
                    id = user.id
            name = body.get('name')
            content = body.get('content')
            type = body.get('type')
            designs = Design.query.all()
            for design in designs:
                if design.userID == id and design.name == name:
                    design.update('',content,type)
                    return f"{design.read()} Updated"
            return f"Cannot locate design", 400
        
        @token_required
        def delete(self, current_user):
            body = request.get_json() # get the body of the request
            token = request.cookies.get("jwt")
            cur_user = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])['_uid']
            users = User.query.all()
            for user in users:
                if user.uid==cur_user: # modified with the and user.id==cur_user so random users can't delete other ppl
                    id = user.id
            name = body.get('name')
            designs = Design.query.all()
            for design in designs:
                if design.userID == id and design.name == name:
                    design.delete()
                    return f"{design.read()} Deleted"
            return f"Cannot locate design", 400

            
            

        
    class _Security(Resource):
        def post(self):
            try:
                body = request.get_json()
                if not body:
                    return {
                        "message": "Please provide user details",
                        "data": None,
                        "error": "Bad request"
                    }, 400
                ''' Get Data '''
                uid = body.get('uid')
                if uid is None:
                    return {'message': f'User ID is missing'}, 400
                password = body.get('password')
                
                ''' Find user '''
                user = User.query.filter_by(_uid=uid).first()
                if user is None or not user.is_password(password):
                    return {'message': f"Invalid user id or password"}, 400
                if user:
                    try:
                        token = jwt.encode(
                            {"_uid": user._uid},
                            current_app.config["SECRET_KEY"],
                            algorithm="HS256"
                        )
                        resp = Response("Authentication for %s successful" % (user._uid))
                        resp.set_cookie("jwt", token,
                                max_age=3600,
                                secure=True,
                                httponly=False,
                                path='/',
                                samesite='None'  # This is the key part for cross-site requests

                                # domain="frontend.com"
                                )
                        return resp
                    except Exception as e:
                        return {
                            "error": "Something went wrong",
                            "message": str(e)
                        }, 500
                return {
                    "message": "Error fetching auth token!",
                    "data": None,
                    "error": "Unauthorized"
                }, 404
            except Exception as e:
                return {
                        "message": "Something went wrong!",
                        "error": str(e),
                        "data": None
                }, 500

            
    # building RESTapi endpoint
    api.add_resource(_CRUD, '/')
    api.add_resource(_DesignCRUD, '/design')
    api.add_resource(_Security, '/authenticate')
    