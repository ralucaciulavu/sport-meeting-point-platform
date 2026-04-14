from datetime import date, time
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import inspect, text

from backend.database import SessionLocal, engine
from backend.models import Base, LocationDB, RegistrationDB

# Create missing tables on startup for the current prototype setup.
Base.metadata.create_all(bind=engine)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="Sport Meeting Point Platform")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


def ensure_registration_columns() -> None:
    inspector = inspect(engine)
    if not inspector.has_table("registrations"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("registrations")}
    if "available_days" in existing_columns and "available_dates" not in existing_columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE registrations "
                    "RENAME COLUMN available_days TO available_dates"
                )
            )
        existing_columns.remove("available_days")
        existing_columns.add("available_dates")

    if "available_dates" not in existing_columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE registrations "
                    "ADD COLUMN available_dates VARCHAR(255) NOT NULL DEFAULT CURRENT_DATE::text"
                )
            )


ensure_registration_columns()


class Location(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class RegistrationCreate(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    phone_number: str = Field(..., min_length=8, max_length=32)
    favorite_sport: str = Field(..., min_length=2, max_length=100)
    available_dates: list[date] = Field(..., min_length=1)
    available_from: time
    available_to: time
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    whatsapp_opt_in: bool

    @field_validator("first_name", "last_name", "favorite_sport")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty.")
        return cleaned

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        cleaned = value.strip()
        # Keep validation permissive for international phone formatting.
        allowed_chars = set("+0123456789 ()-")
        if not cleaned or any(char not in allowed_chars for char in cleaned):
            raise ValueError("Phone number contains invalid characters.")

        digits = "".join(char for char in cleaned if char.isdigit())
        if len(digits) < 8:
            raise ValueError("Phone number must contain at least 8 digits.")
        return cleaned

    @field_validator("available_dates")
    @classmethod
    def validate_available_dates(cls, value: list[date]) -> list[date]:
        if not value:
            raise ValueError("Select at least one available date.")

        unique_dates: list[date] = []
        for selected_date in sorted(value):
            if selected_date not in unique_dates:
                unique_dates.append(selected_date)
        return unique_dates

    @model_validator(mode="after")
    def validate_schedule(self) -> "RegistrationCreate":
        if self.available_from >= self.available_to:
            raise ValueError("available_from must be earlier than available_to.")
        if not self.whatsapp_opt_in:
            raise ValueError("WhatsApp consent is required.")
        return self


class RegistrationResponse(BaseModel):
    id: int
    display_name: str
    favorite_sport: str
    available_dates: list[date]
    available_from: time
    available_to: time


def serialize_registration(registration: RegistrationDB) -> RegistrationResponse:
    display_name = f"{registration.first_name} {registration.last_name[:1].upper()}."
    available_dates: list[date] = []
    for value in registration.available_dates.split(","):
        if not value:
            continue
        try:
            available_dates.append(date.fromisoformat(value))
        except ValueError:
            continue

    return RegistrationResponse(
        id=registration.id,
        display_name=display_name,
        favorite_sport=registration.favorite_sport,
        available_dates=available_dates,
        available_from=registration.available_from,
        available_to=registration.available_to,
    )


@app.get("/")
def home() -> FileResponse:
    # Serve the single-page intake UI from the same FastAPI app.
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {"message": "API is running"}


@app.post("/meeting-point")
def meeting_point(locations: List[Location]) -> dict:
    if not locations:
        raise HTTPException(status_code=400, detail="No locations provided.")

    db = SessionLocal()

    try:
        # Keep the original prototype behavior: persist submitted points.
        for loc in locations:
            db.add(LocationDB(lat=loc.lat, lng=loc.lng))
        db.commit()
    finally:
        db.close()

    lat = sum(point.lat for point in locations) / len(locations)
    lng = sum(point.lng for point in locations) / len(locations)

    return {"lat": lat, "lng": lng}


@app.get("/test-db")
def test_db() -> dict:
    try:
        connection = engine.connect()
        connection.close()
        return {"status": "connected"}
    except Exception as exc:
        return {"error": str(exc)}


@app.get("/locations")
def get_locations() -> list[dict]:
    db = SessionLocal()

    try:
        locations = db.query(LocationDB).all()
        return [
            {
                "id": loc.id,
                "lat": loc.lat,
                "lng": loc.lng,
                "created_at": loc.created_at,
            }
            for loc in locations
        ]
    finally:
        db.close()


@app.post("/api/registrations", response_model=RegistrationResponse, status_code=201)
def create_registration(payload: RegistrationCreate) -> RegistrationResponse:
    db = SessionLocal()

    try:
        # Store the final map pin coordinates, not necessarily the browser-detected ones.
        payload_data = payload.model_dump()
        payload_data["available_dates"] = ",".join(
            selected_date.isoformat() for selected_date in payload_data["available_dates"]
        )
        registration = RegistrationDB(**payload_data)
        db.add(registration)
        db.commit()
        db.refresh(registration)
        return serialize_registration(registration)
    finally:
        db.close()


@app.get("/api/registrations", response_model=list[RegistrationResponse])
def list_registrations() -> list[RegistrationResponse]:
    db = SessionLocal()

    try:
        # Public listing intentionally excludes phone numbers from the response model.
        registrations = db.query(RegistrationDB).order_by(RegistrationDB.created_at.desc()).all()
        return [serialize_registration(registration) for registration in registrations]
    finally:
        db.close()
