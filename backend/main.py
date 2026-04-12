from fastapi import FastAPI

# Create application
app = FastAPI()

# Endpoint route
@app.get("/")
def home():
    return {"message": "API is running"}