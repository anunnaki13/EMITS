# Database connection and utilities
from motor.motor_asyncio import AsyncIOMotorClient
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
_db_name = os.environ.get("MONGO_TEST_DB_NAME") or os.environ['DB_NAME']
db = client[_db_name]

# JWT Settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'tenayan-fuel-management-secret-key-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
