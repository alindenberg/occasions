import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from typing import Annotated
from db.database import get_db
from stripe_utils.services import StripeService
from users.models import User
from users.services import UserService, UserAuthenticationService
from users.types import UserIn, GoogleUserIn, UserOut, CheckoutRequest, FeedbackRequest, RefreshTokenReq
from users.utils import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/users/me", response_model=UserOut)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.get("/users", response_model=list[UserOut])
async def users(current_user: Annotated[User, Depends(get_current_user)], db: Session = Depends(get_db)):
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    return await UserService().get_all_users(db)


@router.post("/google-login")
async def google_login(user: GoogleUserIn, db: Session = Depends(get_db)):
    from users.services import UserAuthenticationService
    try:
        await UserAuthenticationService().google_login(db, user)
        return {"ok": True}
    except Exception as e:
        logger.error(f"An error occurred while logging in: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while logging in")


@router.post("/login")
async def login(user: UserIn, db: Session = Depends(get_db)):
    return await UserAuthenticationService().login(db, user.email, user.password)


@router.post("/signup")
async def signup(user: UserIn, db: Session = Depends(get_db)):
    try:
        return await UserAuthenticationService().signup(db, user)
    except Exception as e:
        logger.error(f"An error occurred while signing up: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/token/refresh")
async def refresh_token(refresh: RefreshTokenReq, db: Session = Depends(get_db)):
    return await UserAuthenticationService().refresh_token(db, refresh.refresh_token)


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


@router.post("/feedback")
async def submit_feedback(
    feedback_request: FeedbackRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    try:
        await UserService().create_feedback(db, feedback_request.feedback, current_user)
        return {"status": "success", "message": "Feedback submitted successfully"}
    except Exception as e:
        logger.error(f"An error occurred while submitting feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while submitting feedback"
        )


@router.get("/verify-email/{token}")
async def verify_email(token: str, db: Session = Depends(get_db)):
    if await UserService().verify_email(db, token):
        return {"message": "Email verified successfully"}
    raise HTTPException(status_code=400, detail="Invalid or expired token")