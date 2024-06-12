from users.models import User

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserService:
    async def create_user(self, db, user):
        db_user = User(
            username=user.username,
            email=user.email,
            password=user.password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    async def get_user(self, db, user_id):
        return db.query(User).get(user_id)

    async def get_user_by_username(self, db, username):
        return db.query(User).filter(User.username == username).first()