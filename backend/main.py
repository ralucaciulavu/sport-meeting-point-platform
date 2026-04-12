from fastapi import FastAPI
from typing import List
from pydantic import BaseModel

# Initialize FastAPI application instance
app = FastAPI()


# Data model representing a geographic location
# FastAPI will use this to validate incoming request data
class Location(BaseModel):
    lat: float  # Latitude coordinate
    lng: float  # Longitude coordinate


# Health check endpoint
# Used to verify that the API is running
@app.get("/")
def home():
    return {"message": "API is running"}


# Endpoint to calculate the optimal meeting point
# Accepts a list of locations and returns their centroid (average point)
@app.post("/meeting-point")
def meeting_point(locations: List[Location]):
    # Validate input: ensure at least one location is provided
    if not locations:
        return {"error": "No locations provided"}

    # Calculate average latitude
    lat = sum(p.lat for p in locations) / len(locations)

    # Calculate average longitude
    lng = sum(p.lng for p in locations) / len(locations)

    # Return the computed meeting point
    return {"lat": lat, "lng": lng}