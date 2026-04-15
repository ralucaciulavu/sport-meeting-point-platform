from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Time
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class LocationDB(Base):
    # Legacy table kept for the original centroid endpoint.
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class RegistrationDB(Base):
    # Main intake entity used by the website flow.
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone_number = Column(String(32), nullable=False)
    favorite_sport = Column(String(100), nullable=False)
    available_dates = Column(String(255), nullable=False)
    available_from = Column(Time, nullable=False)
    available_to = Column(Time, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    whatsapp_opt_in = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
