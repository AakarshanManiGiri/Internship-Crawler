from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import sys
from pathlib import Path as PathLib

sys.path.insert(0, str(PathLib(__file__).parent.parent))

from database.db import Database
from models.internship import Internship

# Initializing FastAPI
app = FastAPI(
    title="Internship Crawler API",
    description="REST API to access internship listings from tech companies",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Database instance
db = Database()

# Pydantic models for request/response
class InternshipResponse(BaseModel):
    id: Optional[int] = None
    company: str
    title: str
    location: Optional[str] = None
    url: str
    posted_date: str
    description: str
    requirements: List[str] = []
    created_at: str
    notified: bool = False

    class Config:
        from_attributes = True

class InternshipsListResponse(BaseModel):
    total: int
    internships: List[InternshipResponse]
    filters: dict = {}

# Endpoints
@app.get("/internships", response_model=InternshipsListResponse)
def get_internships(
    country: Optional[str] = Query(None, description="Filter by country/location"),
    posted_date: Optional[str] = Query(None, description="Filter by date range: 'past_hour', 'past_week', or 'past_month'")
):
    """
    Get all internships with optional filtering by country and date range.
    
    Query Parameters:
    - country: Filter by location/country (case-insensitive)
    - posted_date: Filter by date range ('past_hour', 'past_week', 'past_month')
    
    Returns sorted list of internships in JSON format.
    """
    
    # Validate date_filter parameter
    valid_date_filters = ['past_hour', 'past_week', 'past_month']
    if posted_date and posted_date not in valid_date_filters:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid posted_date filter. Must be one of: {', '.join(valid_date_filters)}"
        )
    
    # Get filtered internships from database
    internships = db.get_internships_with_filters(country=country, date_filter=posted_date)
    
    # Convert to response format
    internship_responses = [
        InternshipResponse(
            id=internship.id,
            company=internship.company,
            title=internship.title,
            location=internship.location,
            url=internship.url,
            posted_date=internship.posted_date.isoformat(),
            description=internship.description,
            requirements=internship.requirements,
            created_at=internship.created_at.isoformat(),
            notified=internship.notified
        )
        for internship in internships
    ]
    
    # Build filters info for response
    filters = {}
    if country:
        filters['country'] = country
    if posted_date:
        filters['posted_date'] = posted_date
    
    return InternshipsListResponse(
        total=len(internship_responses),
        internships=internship_responses,
        filters=filters
    )
