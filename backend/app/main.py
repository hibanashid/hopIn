import os
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app import crud, models, schemas, database, itinerary_generator
from .database import SessionLocal, engine
from dotenv import load_dotenv
import logging
from fastapi.responses import JSONResponse
from pydantic import constr, conint,BaseModel, RootModel, Field
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
import aioredis
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import tenacity
from tenacity import retry, stop_after_attempt, wait_fixed
from typing import List, Optional, Dict

print("Starting application...")  # Debug print

load_dotenv()

print(f"GOOGLE_MAPS_API_KEY: {os.getenv('GOOGLE_MAPS_API_KEY')}")  # Debug print
print(f"Current working directory: {os.getcwd()}")  # Debug print
print(f"Files in current directory: {os.listdir()}")  # Debug print

try:
    # Use absolute imports
    from app import crud, models, schemas, database, itinerary_generator
    print("Imports successful")  # Debug print
except ImportError as e:
    print(f"Import error: {e}")  # Debug print
    raise

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

class Activity(BaseModel):
    time: str
    activity: str
    place_name: str
    description: str
    rating: Optional[float]
    review: str
    google_maps_url: str
    website_url: Optional[str]
    estimated_travel_time: str
    location: Dict[str, float]
    distance_to_next: Optional[str]

class DayItinerary(BaseModel):
    activities: List[Activity]

class FullItinerary(BaseModel):
    itinerary: Dict[str, DayItinerary]

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://redis", encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    await FastAPILimiter.init(redis)

@app.get("/generate_itinerary/", response_model=FullItinerary)
@app.post("/generate_itinerary/", response_model=FullItinerary)
@cache(expire=3600)
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def generate_itinerary(
    destination: constr(min_length=1, max_length=100) = Query(..., description="Destination city"),
    no_of_days: conint(ge=1, le=14) = Query(..., description="Number of days for the trip"),
    food_preference: constr(min_length=1, max_length=100) = Query(..., description="Food preference"),
    rate_limiter: RateLimiter = Depends(RateLimiter(times=10, seconds=60))
):
    try:
        logger.info(f"Generating itinerary for {destination}, {no_of_days} days, {food_preference}")
        itinerary_data = itinerary_generator.generate_itinerary(
            destination=destination,
            no_of_days=no_of_days,
            food_preference=food_preference
        )
        logger.debug(f"Generated itinerary: {itinerary_data}")
        if itinerary_data is None:
            logger.error("Generated itinerary is None")
            raise HTTPException(status_code=500, detail="Failed to generate itinerary: Itinerary data is None")
        # Restructure the data to match the FullItinerary model
        structured_itinerary = {
            day: DayItinerary(activities=activities)
            for day, activities in itinerary_data.items()
        }
        return FullItinerary(itinerary=structured_itinerary)
    except Exception as e:
        logger.exception(f"Error generating itinerary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate itinerary: {str(e)}")

@app.post("/itineraries/", response_model=schemas.Itinerary)
def create_itinerary(itinerary: schemas.ItineraryCreate, user_id: int, db: Session = Depends(get_db)):
    return crud.create_itinerary(db=db, itinerary=itinerary, user_id=user_id)

@app.get("/itineraries/{itinerary_id}", response_model=schemas.Itinerary)
def read_itinerary(itinerary_id: int, db: Session = Depends(get_db)):
    db_itinerary = crud.get_itinerary(db, itinerary_id=itinerary_id)
    if db_itinerary is None:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return db_itinerary

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.get("/test_itinerary/")
async def test_itinerary():
    logger.debug("Accessing test_itinerary endpoint")
    try:
        itinerary_data = itinerary_generator.generate_itinerary(
            destination="Paris",
            no_of_days=3,
            food_preference="French cuisine"
        )
        logger.debug(f"Generated itinerary: {itinerary_data}")
        if itinerary_data is None:
            logger.error("Generated itinerary is None")
            raise HTTPException(status_code=500, detail="Failed to generate itinerary")
        return JSONResponse(content=itinerary_data)
    except Exception as e:
        logger.error(f"Error generating itinerary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

print("Application initialized")  # Debug print

@app.get("/test_google_maps/")
async def test_google_maps():
    try:
        result = itinerary_generator.get_places("Tokyo", "tourist attraction")
        return {"result": result}
    except Exception as e:
        logger.exception(f"Error testing Google Maps API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Google Maps API test failed: {str(e)}")

@app.get("/test_gemini/")
async def test_gemini():
    try:
        model = itinerary_generator.GenerativeModel('gemini-1.5-pro-002')
        response = model.generate_content("Generate a short itinerary for Tokyo")
        return {"result": response.text}
    except Exception as e:
        logger.exception(f"Error testing Gemini model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Gemini model test failed: {str(e)}")

@app.get("/test_ors/")
async def test_ors():
    try:
        origin = {"lat": 35.6895, "lng": 139.6917}  # Tokyo coordinates
        destination = {"lat": 35.6762, "lng": 139.6503}  # Shinjuku coordinates
        distance = itinerary_generator.calculate_distance(origin, destination)
        return {"distance": distance}
    except Exception as e:
        logger.exception(f"Error testing ORS API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ORS API test failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
