from datetime import timedelta
from jwt.exceptions import InvalidTokenError
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated
from pydantic import BaseModel, EmailStr


from db.database import engine, get_db
from occasions import models as occasion_models
from occasions import routes as occasion_routes
from users import models as user_models
from users import routes as user_routes

# Create tables
occasion_models.Base.metadata.create_all(bind=engine)
user_models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(occasion_routes.router)
app.include_router(user_routes.router)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.get("/")
async def root():
    return {"message": "Hello World"}
