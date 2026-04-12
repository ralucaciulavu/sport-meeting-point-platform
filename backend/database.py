# Import required modules
import os  # used to access environment variables (e.g., DATABASE_URL)
from sqlalchemy import create_engine  # creates the database engine (connection)
from sqlalchemy.orm import sessionmaker  # used to create database sessions
from dotenv import load_dotenv  # loads variables from a .env file

# Load environment variables from .env file
load_dotenv()

# Get the database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# Create the database engine (main connection to the database)
engine = create_engine(DATABASE_URL)

# Create a session factory for interacting with the database
# Each session represents a conversation/transaction with the DB
SessionLocal = sessionmaker(bind=engine)