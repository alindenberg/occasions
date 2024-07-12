import logging
import os
import stripe

from db.database import get_db
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv('STRIPE_API_KEY')


class StripeService:
    def process_webhook_event(self, db: Session, payload: str, stripe_signature: str):
        event = self._get_event(payload, stripe_signature)

        # Handle the checkout.session.completed event
        if event['type'] == 'checkout.session.completed':

            # Retrieve the session. If you require line items in the response, you may include them by expanding line_items.
            session = stripe.checkout.Session.retrieve(
                event['data']['object']['id'],
                expand=['line_items'],
            )
            self.fulfill_order(db, session)

    def fulfill_order(self, db: Session, session):
        try:
            customer_id = session['customer']
            if not customer_id:
                logger.error("No customer id found in stripe session")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No customer id found in stripe session")
            quantity = session['line_items']['data'][0]['quantity']

            from users.models import StripeCustomer
            customer = db.query(StripeCustomer).filter(StripeCustomer.stripe_customer_id == customer_id).first()
            if not customer:
                logger.error(f"No user found for customer id: {customer_id}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user found for customer id")

            customer.user.add_credits(quantity)
            db.commit()
        except Exception as e:
            logger.error(f"An error occurred while fulfilling order: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while fulfilling order")

    def _get_event(self, payload: str, stripe_signature: str):
        try:
            return stripe.Webhook.construct_event(payload, stripe_signature, os.getenv('STRIPE_WEBHOOK_SECRET'))
        except ValueError as e:
            logger.error(f"Invalid payload for stripe webhook. Error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            logger.error(f"Invalid signature for stripe webhook. Error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    def create_customer_for_user(self, user):
        from users.models import StripeCustomer

        db = next(get_db())

        customer = stripe.Customer.create(email=user.email)
        stripe_customer = StripeCustomer(user_id=user.id, stripe_customer_id=customer.id)
        db.add(stripe_customer)
        db.commit()
        db.refresh(stripe_customer)
        return stripe_customer

    def create_checkout_session(self, user, quantity):
        return stripe.checkout.Session.create(
            ui_mode='embedded',
            customer=user.get_stripe_customer().stripe_customer_id,
            line_items=[
                {
                    'price': os.getenv('STRIPE_PRICE_ID', None),
                    'quantity': quantity
                },
            ],
            mode='payment',
            return_url=f"{os.getenv('NEXT_PUBLIC_URL', 'http://localhost:3000')}/complete" + "?session_id={CHECKOUT_SESSION_ID}",
            automatic_tax={'enabled': False}
        )
