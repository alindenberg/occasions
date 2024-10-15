import asyncio
import logging
from datetime import datetime, timezone, timedelta

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from sqlalchemy import and_
from sqlalchemy.orm import Session

from config import get_settings
from mail.services import MailService

from occasions.constants import LLM_PROMPT
from occasions.models import Occasion
from occasions.types import OccasionTone, OccasionType
from users.models import User


logger = logging.getLogger(__name__)
settings = get_settings()


class OccasionService:
    def create_occasion(self, db: Session, user: User, **kwargs):
        try:
            if not (hasattr(user, 'credits') and user.credits.credits):
                raise ValueError("User has no credits to create an occasion")

            kwargs["date"] = kwargs["date"].isoformat() if kwargs.get("date") else None
            kwargs["created"] = datetime.now(timezone.utc).isoformat()
            kwargs["user_id"] = user.id
            kwargs["email"] = user.email
            occasion = Occasion(**kwargs)
            self._validate_occasion(db, occasion)
            db.add(occasion)

            user.credits.credits -= 1
            db.commit()
            db.refresh(occasion)

            return occasion
        except (ValueError, Exception):
            db.rollback()
            raise

    def get_occasions_for_user(self, db: Session, user_id: int):
        return db.query(Occasion).filter(Occasion.user_id == user_id).all()

    def get_occasion(self, db: Session, occasion_id: int, user_id: int):
        occasion = db.query(Occasion).filter(
            Occasion.id == occasion_id,
            Occasion.user_id == user_id
        ).first()

        if not occasion:
            raise ValueError("Occasion not found")
        return occasion

    def update_occasion(self, db: Session, occasion_id: int, **kwargs):
        occasion = db.query(Occasion).get(occasion_id)
        for key, value in kwargs.items():
            if key == "date":
                value = value.isoformat() if value else None
            setattr(occasion, key, value)
        self._validate_occasion(db, occasion)
        db.commit()
        db.refresh(occasion)
        return occasion

    def delete_occasion(self, db: Session, occasion_id: int):
        # TODO: validate occasion isnt processed yet
        # TODO: add back a user credi't
        occasion = db.query(Occasion).get(occasion_id)
        occasion.user.add_credits(1)
        db.delete(occasion)
        db.commit()
        return {"message": "Occasion deleted successfully"}

    async def process_occasion(self, db: Session, occasion: Occasion):
        try:
            if occasion.date_processed:
                logger.warning(f"Occasion {occasion.id} has already been processed")
                return

            if occasion.is_draft:
                logger.warning(f"Occasion {occasion.id} is in draft state and cannot be processed")
                return

            logger.info(f"Processing occasion {occasion.id}")
            summary = await self._generate_summary(occasion)

            occasion.summary = summary
            occasion.date_processed = datetime.now(timezone.utc).isoformat()
            db.commit()

            asyncio.create_task(self._send_summary(occasion.user.email, occasion.label, summary))

            if occasion.is_recurring:
                self._create_is_recurring_occasion(db, occasion)

            logger.info(f"Occasion {occasion.id} processed successfully")
        except Exception as exc:
            logger.error(f"Error processing occasion {occasion.id}. {exc}")
            db.rollback()

    def _create_is_recurring_occasion(self, db: Session, original_occasion: Occasion):
        try:
            user = db.query(User).get(original_occasion.user_id)

            new_occasion = Occasion(
                    label=original_occasion.label,
                    type=original_occasion.type,
                    tone=original_occasion.tone,
                    email=original_occasion.email,
                    date=(datetime.fromisoformat(original_occasion.date) + timedelta(days=365)).isoformat(),
                    custom_input=original_occasion.custom_input,
                    user_id=original_occasion.user_id,
                    is_recurring=original_occasion.is_recurring,
                    created=datetime.now(timezone.utc).isoformat(),
                    is_draft=True
                )
            if user.credits.credits > 0:
                new_occasion.is_draft = False
                user.credits.credits -= 1

            db.add(new_occasion)
            db.commit()
            logger.info(f"Created {'draft' if new_occasion.is_draft else 'recurring'} occasion {new_occasion.id} for original occasion {original_occasion.id}")
        except Exception as exc:
            logger.error(f"Error creating recurring occasion for {original_occasion.id}. {exc}")
            db.rollback()

    async def _send_summary(self, recipient_email, occasion_label, summary):
        subject = f"Occasion Alerts - Summary for {occasion_label}"
        MailService().send_email(recipient_email, subject, body=summary)

    async def _generate_summary(self, occasion: Occasion):
        model = ChatOpenAI(model='gpt-4o-mini')
        prompt = PromptTemplate(
            input_variables=["occasion_label" "occasion_date", "occasion_tone", "occasion_type", "custom_input"],
            template=LLM_PROMPT
        )
        output_parser = StrOutputParser()

        chain = prompt | model | output_parser

        return await chain.ainvoke({
            "occasion_label": occasion.label,
            "occasion_date": occasion.date,
            "occasion_type": occasion.type,
            "occasion_tone": occasion.tone,
            "custom_input": occasion.custom_input
        })

    def _validate_occasion(self, db: Session, occasion: Occasion):
        self._validate_occasion_tone(occasion)
        self._validate_occasion_type(occasion)

    def _validate_occasion_tone(self, occasion: Occasion):
        for tone in OccasionTone:
            if occasion.tone == tone.value:
                return
        raise ValueError("Invalid occasion tone")

    def _validate_occasion_type(self, occasion: Occasion):
        for occasion_type in OccasionType:
            if occasion.type == occasion_type.value:
                return
        raise ValueError("Invalid occasion type")

    def activate_draft_occasion(self, db: Session, occasion_id: int, user: User):
        occasion = db.query(Occasion).get(occasion_id)
        if not occasion or occasion.user_id != user.id:
            raise ValueError("Occasion not found or doesn't belong to the user")

        if not occasion.is_draft:
            raise ValueError("Occasion is not in draft state")

        if user.credits.credits <= 0:
            raise ValueError("Insufficient credits to activate the occasion")

        occasion.is_draft = False
        user.credits.credits -= 1
        db.commit()
        return occasion
