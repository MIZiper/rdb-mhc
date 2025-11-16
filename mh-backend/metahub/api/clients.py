from fastapi import APIRouter, Depends
from metahub.db.connection import get_db

router = APIRouter()