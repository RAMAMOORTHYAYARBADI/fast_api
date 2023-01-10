
from datetime import timedelta,datetime

from pymongo import MongoClient

import bcrypt
import graphene
from fastapi import FastAPI
from graphql import GraphQLError
from jwt import PyJWTError
from starlette.graphql import GraphQLApp
from apscheduler.schedulers.background import BackgroundScheduler

import models
from db_conf import db_session
from jwt_token import create_access_token, decode_access_token
from schemas import UserSchema, UserModel

from utils import get_active_fb_info, get_enhancement, get_all_enhancement

from pydantic import BaseModel

MONGO_DB = "fast_api"
MSG_COLLECTION = "fast_Api_collection"

db = db_session.session_factory()

sched = BackgroundScheduler(timezone="Asia/kolkata")

app = FastAPI()


class Query(graphene.ObjectType):

    all_posts = graphene.List(UserModel)
    post_by_id = graphene.Field(UserModel, post_id=graphene.Int(required=True))

    def resolve_all_posts(self, info):
        query = UserModel.get_query(info)
        return query.all()

    def resolve_post_by_id(self, info, post_id):
        return db.query(models.Post).filter(models.User.id == post_id).first()


class AuthenticateUser(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    ok = graphene.Boolean()
    token = graphene.String()

    @staticmethod
    def mutate(root, info, email, password):
        user = UserSchema(email=email, password=password)
        db_user_info = db.query(models.User).filter(models.User.email == email).one_or_none()
        if db_user_info is None:
            raise GraphQLError("No user Found")
        if bcrypt.checkpw(user.password.encode("utf-8"), db_user_info.password.encode("utf-8")):
            access_token_expires = timedelta(minutes=60)
            access_token = create_access_token(data={"user": email}, expires_delta=access_token_expires)
            ok = True
            return AuthenticateUser(ok=ok, token=access_token)
        else:
            ok = False
            return AuthenticateUser(ok=ok)

class CreateNewUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    ok = graphene.Boolean()
    message = graphene.String()

    @staticmethod
    def mutate(root, info, email, password,username):

        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        password_hash = hashed_password.decode("utf8")
        user_info = db.query(models.User).filter(models.User.email == email).one_or_none()
        if user_info is not None:
            raise GraphQLError("Already register this email")
        user = UserSchema(email=email, password=password_hash)
        db_user = models.User(email=user.email, password=password_hash,username=username)
        db.add(db_user)
        try:
            db.commit()
            db.refresh(db_user)
            ok = True
            message = "User Create successfully"
            return CreateNewUser(ok=ok,message=message)

        except:
            db.rollback()
            raise      
        db.close()


class PostAccount_details(graphene.Mutation):
    class Arguments:
        account_name  = graphene.String(required=True)
        account_id = graphene.String(required=True)
        token = graphene.String(required=True)

    result = graphene.String()

    @staticmethod
    def mutate(root, info, account_name, account_id, token):

        try:
            payload = decode_access_token(data=token)
            email = payload.get("user")

            if email is None:
                raise GraphQLError("Invalid credentials 1")

        except PyJWTError:
            raise GraphQLError("Invalid credentials 2")

        user = db.query(models.User).filter(models.User.email == email).first()

        if user is None:
            raise GraphQLError("Invalid credentials 3")
        with MongoClient() as client:
            msg_collection = client[MONGO_DB][MSG_COLLECTION]
            data = {
                "account_name":account_name,
                "account_id":account_id
            }
            result = msg_collection.insert_one(data)
            print(result)
            ack = result.acknowledged
            result ="Account Details addded successfully"
            return PostAccount_details(result=result)
       
class PostMutations(graphene.ObjectType):
    authenticate_user = AuthenticateUser.Field()
    create_new_user = CreateNewUser.Field()
    PostAccount_details = PostAccount_details.Field()

@app.get("/api/get_active_fb_info")
async def root():
    data = get_active_fb_info()
    return data

class enhancement_payload(BaseModel):
    from_date: str
    to_date: str


@app.post("/api/get_latest_enhancement")
async def get_latest_enhancement(item:enhancement_payload ):
    dict_item = item.dict()
    from_date = dict_item['from_date']
    to_date = dict_item['to_date']
    data = get_enhancement(from_date,to_date)
    return data

def job1():
    data = get_all_enhancement()
    with MongoClient() as client:
        msg_collection = client[MONGO_DB][MSG_COLLECTION]
        result = msg_collection.insert_one(data) 
        ack = result.acknowledged

def job2():
    data = get_all_enhancement()
    with MongoClient() as client:
        msg_collection = client[MONGO_DB][MSG_COLLECTION]
        result = msg_collection.insert_one(data)
        ack = result.acknowledged

@app.on_event('startup')
def init_data():
    sched.add_job(job1, 'cron', hour=2, minute=30)
    sched.add_job(job2, 'cron', hour=14, minute=30)
    sched.start()

app.add_route("/graphql", GraphQLApp(schema=graphene.Schema(query=Query, mutation=PostMutations)))
