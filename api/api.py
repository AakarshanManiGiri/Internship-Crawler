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