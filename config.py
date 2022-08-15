import os
from dotenv import load_dotenv
load_dotenv()


LOCALHOST_URI = os.getenv('LOCALHOST_DATABASE_URI')
HEROKU_URI = os.getenv('HEROKU_DATABASE_URI')
SECRET_KEY = os.getenv('APP_SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')

