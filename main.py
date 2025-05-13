from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pymongo import MongoClient
from typing import Optional
import os
from dotenv import load_dotenv

from .models import UserInDB, Statement
from .schemas import UserCreate, UserLogin, SpendData, GmailAuth
from .auth import get_current_user, create_access_token, authenticate_user, get_password_hash, verify_password
from .gmail import process_gmail_auth, fetch_estatement
from .prediction import recommend_card

load_dotenv()

app = FastAPI(title="Maxx Mai Card Recommender")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = client["card_recommender"]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    if db.users.find_one({"email": user.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user.password)
    user_dict = user.dict()
    user_dict["hashed_password"] = hashed_password
    del user_dict["password"]
    
    db.users.insert_one(user_dict)
    return {"message": "User created successfully"}

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/gmail-auth")
async def gmail_auth(auth: GmailAuth, current_user: dict = Depends(get_current_user)):
    credentials = process_gmail_auth(auth.code)
    estatement_data = fetch_estatement(credentials)
    
    statement = Statement(
        user_email=current_user.email,
        data=estatement_data,
        processed=False
    )
    db.statements.insert_one(statement.dict())
    
    return {"message": "eStatement processed successfully", "data": estatement_data}

@app.post("/recommend")
async def recommend(spend_data: SpendData, current_user: dict = Depends(get_current_user)):
    recommendation = recommend_card(spend_data.dict())
    return {"recommendation": recommendation}

@app.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    user = db.users.find_one({"email": current_user["email"]}, {"hashed_password": 0})
    return user
