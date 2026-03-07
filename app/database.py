from sqlalchemy import create_engine #create all actual connection to db
from sqlalchemy.ext.declarative import declarative_base #base class all models inherits from
from sqlalchemy.orm import sessionmaker # create db session, (like opening/closing conversation with db)
import os
from dotenv import load_dotenv #reads .ev file so python can access secret variables

load_dotenv() #reads .env file

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./skincare.db") #looks for db url in .env, if it cant find, it'll fall to sqlite:///./skincare.db
# sqlite:///./skincare.db = "create a SQLite database fike calle skincare.db incurrent folder"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}) #engine= actual db connection, check_same_thread": False ->

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # no autocommit, so nothing saves to db automatically, autoflash=false -> wont auto sync changes mid session
#bind=engine -> connects this session factory to your database engine

Base = declarative_base() #parent class all models will inherit from |template for model


def get_db():
    db = SessionLocal() #opens a fresh db session
    try:
        yield db #passes it to endpoint function
    finally:
        db.close() #after endpoint finishes, finally runs and closes session (db wont be left open forever)