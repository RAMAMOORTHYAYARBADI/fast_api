from graphene_sqlalchemy import SQLAlchemyObjectType
from pydantic import BaseModel

from models import User


class UserModel(SQLAlchemyObjectType):
    class Meta:
        model = User


class UserSchema(BaseModel):
    email: str
    password: str
        