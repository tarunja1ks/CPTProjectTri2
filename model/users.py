""" database dependencies to support sqliteDB examples """
from random import randrange
from datetime import date
import os, base64
import json

from __init__ import app, db
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash


''' Tutorial: https://www.sqlalchemy.org/library.html#tutorials, try to get into Python shell and follow along '''

# Define the Post class to manage actions in 'posts' table,  with a relationship to 'users' table
class Design(db.Model):
    __tablename__ = 'designs'

    name = db.Column(db.String, unique=False, primary_key=True)
    type = db.Column(db.Text, unique=False, nullable=False)
    content = db.Column(db.String, unique=False)
    # Define a relationship in Notes Schema to userID who originates the note, many-to-one (many notes to one user)
    userID = db.Column(db.Integer, db.ForeignKey('users.id'))
    likes = db.Column(db.Integer, unique=False, nullable=False)
    dislikes = db.Column(db.Integer, unique=False, nullable=False)
    def __init__(self, id, type, content, name, likes=0, dislikes=0, description=""):
        self.userID = id
        self.type = type
        self.content = content
        self.name = name
        self.likes = likes
        self.dislikes = dislikes
        self.description = description

    # Returns a string representation of the Notes object, similar to java toString()
    # returns string
    def __repr__(self):
        return {"Name": self.name, "Content": self.content, "Type": self.type, "Owner": self.userID, "Likes": self.likes, "Dislikes": self.dislikes, "Description": self.description,}

    # CRUD create, adds a new record to the Notes table
    # returns the object added or None in case of an error
    def create(self):
        try:
            # creates a Notes object from Notes(db.Model) class, passes initializers
            db.session.add(self)  # add prepares to persist person object to Notes table
            db.session.commit()  # SqlAlchemy "unit of work pattern" requires a manual commit
            return self
        except IntegrityError:
            db.session.remove()
            return None

    # CRUD read, returns dictionary representation of Notes object
    # returns dictionary
    def read(self):
        
        return {
            "Name": self.name,
            "Owner": self.userID,
            "Content": self.content,
            "Type": self.type,
            "Likes": self.likes,
            "Dislikes": self.dislikes,
            "Description": self.description,
        }
    
    def update(self, name="", content="", type="", likes=0, dislikes=0, description=''):
        """only updates values with length"""
        if len(name) > 0:
            self.name = name
        if len(content) > 0:
            self.content = content
        if len(type) > 0:
            self.type = type
        if likes != 0:
            self.likes += likes
        if dislikes != 0:
            self.dislikes += dislikes
        if len(description) != 0:
            self.description = description
        db.session.commit()
        return self
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return None

# Define the User class to manage actions in the 'users' table
# -- Object Relational Mapping (ORM) is the key concept of SQLAlchemy
# -- a.) db.Model is like an inner layer of the onion in ORM
# -- b.) User represents data we want to store, something that is built on db.Model
# -- c.) SQLAlchemy ORM is layer on top of SQLAlchemy Core, then SQLAlchemy engine, SQL
class User(db.Model):
    __tablename__ = 'users'  # table name is plural, class name is singular

    # Define the User schema with "vars" from object
    id = db.Column(db.Integer, primary_key=True)
    _name = db.Column(db.String(255), unique=False, nullable=False)
    _uid = db.Column(db.String(255), unique=True, nullable=False)
    _password = db.Column(db.String(255), unique=False, nullable=False)
    _type = db.Column(db.String(255), unique=False, nullable=False)
    _dob = db.Column(db.Date)
    images = db.Column(db.String, unique=False)
    # Defines a relationship between User record and Notes table, one-to-many (one user to many notes)
    designs = db.relationship("Design", cascade='all, delete', backref='users', lazy=True)

    # constructor of a User object, initializes the instance variables within object (self)
    def __init__(self, name, uid,images, password="123qwerty", type="standard" ):
        self._name = name    # variables with self prefix become part of the object, 
        self._uid = uid
        self.set_password(password)
        self._type = type
        self.images=images

    # a name getter method, extracts name from object
    @property
    def name(self):
        return self._name
    
    # a setter function, allows name to be updated after initial object creation
    @name.setter
    def name(self, name):
        self._name = name
    
    # a getter method, extracts email from object
    @property
    def uid(self):
        return self._uid
    
    # a setter function, allows name to be updated after initial object creation
    @uid.setter
    def uid(self, uid):
        self._uid = uid
        
    # check if uid parameter matches user id in object, return boolean
    def is_uid(self, uid):
        return self._uid == uid
    
    @property
    def password(self):
        return self._password[0:10] + "..." # because of security only show 1st characters

    # update password, this is conventional setter
    def set_password(self, password):
        """Create a hashed password."""
        self._password = generate_password_hash(password, "pbkdf2:sha256", salt_length=10)

    # check password parameter versus stored/encrypted password
    def is_password(self, password):
        """Check against hashed password."""
        result = check_password_hash(self._password, password)
        return result

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, type):
        self._type = type
    
    # output content using str(object) in human readable form, uses getter
    # output content using json dumps, this is ready for API response
    def __str__(self):
        return json.dumps(self.read())

    # CRUD create/add a new record to the table
    # returns self or None on error
    def create(self):
        try:
            # creates a person object from User(db.Model) class, passes initializers
            db.session.add(self)  # add prepares to persist person object to Users table
            db.session.commit()  # SqlAlchemy "unit of work pattern" requires a manual commit
            return self
        except IntegrityError:
            db.session.remove()
            return None

    # CRUD read converts self to dictionary
    # returns dictionary
    def read(self):
        return {
            "id": self.id,
            "name": self.name,
            "uid": self.uid,
            "type": self.type,
            "designs": [design.read() for design in self.designs]
        }
    

    # CRUD update: updates user name, password, phone
    # returns self
    def update(self, name="", uid="", password=""):
        """only updates values with length"""
        if len(name) > 0:
            self.name = name
        if len(uid) > 0:
            self.uid = uid
        if len(password) > 0:
            self.set_password(password)
        
        db.session.commit()
        return self
    def updatepfp(self,image64=""):
        if(len(image64)>0):
            self.images=image64
        db.session.commit()
        return self

    # CRUD delete: remove self
    # None
    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return None


"""Database Creation and Testing """


# Builds working data for testing
def initUsers():
    with app.app_context():
        """Create database and tables"""
        db.create_all()
        """Tester data for table"""
        u1 = User(name='Thomas Edison', uid='toby', password='123toby', type="admin",images="thing")
        u2 = User(name='Nicholas Tesla', uid='niko', password='123niko', type="standard",images="thing")
        u3 = User(name='Alexander Graham Bell', uid='lex', type="standard",images="thing")
        u4 = User(name='Grace Hopper', uid='hop', password='123hop', type="standard",images="thing")
        users = [u1, u2, u3, u4]

        """Builds sample user/note(s) data"""
        for user in users:
            try:
                '''add a few 1 to 4 notes per user'''
                '''add user/post data to table'''
                user.create()
            except IntegrityError:
                '''fails with bad or duplicate data'''
                db.session.remove()
                print(f"Records exist, duplicate email, or error: {user.uid}")
            