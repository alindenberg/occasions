import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated
from db.database import get_db

from stripe_utils.services import StripeService
from users.exceptions import UserNotFoundException
from users.models import User
from users.services import UserService, UserAuthenticationService
from users.types import UserIn, UserOut, CheckoutRequest, PasswordResetRequest, PasswordReset
from users.utils import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/users/me", response_model=UserOut)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.get("/users", response_model=list[UserOut])
async def users(db: Session = Depends(get_db)):
    return await UserService().get_all_users(db)


@router.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    try:
        token = await UserAuthenticationService().login(db, form_data)
        return {"access_token": token, "token_type": "bearer"}
    except UserNotFoundException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    except Exception as e:
        logger.error(f"An error occurred while logging in: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while logging in")


@router.post("/signup")
async def signup(user: UserIn, db: Session = Depends(get_db)):
    try:
        token = await UserAuthenticationService().signup(db, user)
        return {"access_token": token, "token_type": "bearer"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"An error occurred while signing up - {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while signing up")


@router.post("/stripe-webhook")
async def stripe_webhook(
        stripe_signature: Annotated[str, Header(alias="stripe-signature")],
        request: Request,
        db: Session = Depends(get_db)):
    try:
        payload = await request.body()
        StripeService().process_webhook_event(db, payload, stripe_signature)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"An error occurred while processing the Stripe webhook: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while processing the webhook")


@router.post("/checkout")
async def checkout(user: Annotated[User, Depends(get_current_user)], request: CheckoutRequest):
    try:
        session = StripeService().create_checkout_session(user, request.quantity)
        return {"client_secret": session.client_secret}
    except Exception as e:
        logger.error(f"An error occurred while creating checkout session: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while creating checkout session")


@router.post("/request-password-reset", status_code=status.HTTP_200_OK)
async def request_password_reset(request: PasswordResetRequest, db: Session = Depends(get_db)):
    logger.info(f"Requesting password reset for {request.email}")
    user = await UserService().get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserAuthenticationService().generate_reset_hash(db, user)


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(request: PasswordReset, db: Session = Depends(get_db)):
    return UserAuthenticationService().reset_password(db, request.reset_hash, request.new_password)