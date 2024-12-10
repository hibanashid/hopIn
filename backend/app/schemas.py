from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class UserLogin(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

class ItineraryRequest(BaseModel):
    destination: str
    no_of_days: int
    food_preference: str

class ActivityDetail(BaseModel):
    time: str
    activity: str
    place_name: str
    description: str
    rating: float
    review: str
    google_maps_url: str
    website_url: Optional[str]
    estimated_travel_time: str
    location: Dict[str, float]
    distance_to_next: Optional[str]

class ItineraryDay(BaseModel):
    activities: List[ActivityDetail]

class ItineraryCreate(BaseModel):
    days: Dict[str, List[ActivityDetail]]

class Itinerary(ItineraryCreate):
    id: int
    owner_id: int

    class Config:
        from_attributes = True
