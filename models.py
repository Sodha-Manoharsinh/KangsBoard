from peewee import *
from datetime import datetime

db = SqliteDatabase('project_wall.db')

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    username = CharField(unique=True)
    email = CharField(unique=True)
    password = CharField()

    user_description = TextField(null=True)
    skills = TextField(null=True)

    total_views = IntegerField(default=0)
    has_project = BooleanField(default=False)
    isOnline = BooleanField(default=False)
    last_seen = TextField(null=True)

class Project(BaseModel):
    title = CharField(unique=True)  
    description = TextField()
    technologies = TextField()

    github_link = CharField(unique=True)
    host_link = CharField(null=True)  

    views = IntegerField(default=0)
    created_at = DateTimeField(default=datetime.now)

    user = ForeignKeyField(User, backref='projects', on_delete='CASCADE')


db.connect()
db.create_tables([User,Project])

