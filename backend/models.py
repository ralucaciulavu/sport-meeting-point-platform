from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

# Base class for all database models
# SQLAlchemy uses this to map Python classes to database tables
Base = declarative_base()

class LocationDB(Base):
    # Name of the table in PostgreSQL
    __tablename__ = "locations"

    # Primary key (unique ID for each row)
    id = Column(Integer, primary_key=True, index=True)

    # Latitude of the location
    lat = Column(Float, nullable=False)

    # Longitude of the location
    lng = Column(Float, nullable=False)

    # Timestamp when the record was created
    # Default = current time when row is inserted
    created_at = Column(DateTime, default=datetime.utcnow)