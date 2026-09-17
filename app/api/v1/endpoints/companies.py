# app/api/v1/endpoints/companies.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_companies():
    return [
        "Hub Myanmar", 
        "On Doctor",
        "Pan Set Lann", 
        "First Step Global",
        "Kyal Sin Akhaya", 
        "Biota Myanamr", 
        "Twa Win Akariz",
        "Pan Asia Partners", 
        "Pacific Rise Group", 
        "Horizon Marinen Energy", 
        "Unity Business Partners", 
        "Apex Care", 
        "Premium Capital Group", 
        "Eastern Valley Partners"
    ]