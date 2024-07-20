import asyncio
import logging

from datetime import datetime, timezone
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from sqlalchemy import and_
from sqlalchemy.orm import Session

from config import get_settings
from mail.services import MailService
from occasions.constants import LLM_PROMPT
from occasions.models import Occasion
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
            db.commit()
            db.refresh(occasion)

            try:
                user.credits.credits -= 1
                db.commit()
            except Exception as exc:
                logger.error(f"Error updating credits for user {user.id}. {exc}")

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

            logger.info(f"Processing occasion {occasion.id}")
            summary = await self._generate_summary(occasion)

            occasion.summary = summary
            occasion.date_processed = datetime.now(timezone.utc).isoformat()
            db.commit()

            asyncio.create_task(self._send_summary(occasion.user.email, occasion.label, summary))

            logger.info(f"Occasion {occasion.id} processed successfully")
        except Exception as exc:
            logger.error(f"Error processing occasion {occasion.id}. {exc}")
            db.rollback()

    async def _send_summary(self, recipient_email, occasion_label, summary):
        subject = f"Occasion Alerts - Summary for {occasion_label}"
        MailService().send_email(recipient_email, subject, body=summary)

    async def _generate_summary(self, occasion: Occasion):
        model = ChatOpenAI(model='gpt-4o-mini')
        prompt = PromptTemplate(
            input_variables=["occasion_label" "occasion_date", "occasion_type", "custom_input"],
            template=LLM_PROMPT
        )
        output_parser = StrOutputParser()

        chain = prompt | model | output_parser

        return await chain.ainvoke({
            "occasion_label": occasion.label,
            "occasion_date": occasion.date,
            "occasion_type": occasion.type,
            "custom_input": occasion.custom_input
        })

    def _validate_occasion(self, db: Session, occasion: Occasion):
        current_time = datetime.now(timezone.utc)
        existing_occasions = db.query(Occasion).filter(
            and_(
                Occasion.user_id == occasion.user_id,
                Occasion.id != occasion.id,
                Occasion.date >= current_time.isoformat()
            )
        ).count()
        if existing_occasions >= 3:
            raise ValueError("User can only have 3 upcoming occasions")
