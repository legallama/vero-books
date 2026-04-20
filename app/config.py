import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-very-secret')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/verobooks')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Custom config for tenancy
    TENANT_URL_PREFIX = '/<org_id>'
