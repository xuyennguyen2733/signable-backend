import logging
import os
import jwt
import random
from pydantic import BaseModel
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session
from passlib.context import CryptContext
from sqlmodel import Session, select

import database as db
from entities.database_entities import Users

import smtplib
from email.message import EmailMessage
import ssl

import database as db
from entities.user_entities import (
    DateResponse,
    PermissionsResponse,
    ProgressResponse,
    ProgressUpdate,
    XpResponse,
    UserResponse,
    UserUpdate,
    FollowersResponse,
    UserRegistration,
    PasswordUpdate
)

users_router = APIRouter(prefix="/users", tags=["Users"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
access_token_duration = 3600  # seconds
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")
JWT_KEY = os.environ.get("JWT_KEY", default="insecure-jwt-key-for-dev")
JWT_ALG = "HS256"

LESSON_XP_AMOUNT = 10


# This silences a warning that will show up because of bcrypt/passlib versioning: https://github.com/pyca/bcrypt/issues/684
logging.getLogger('passlib').setLevel(logging.ERROR)

##                  ##
##  Register User   ##
##                  ##

@users_router.post("/signup", response_model=UserResponse)
def create_user(registration: UserRegistration, 
                session: Session = Depends(db.get_session)):
      """Register New User"""
      try:
        registration.password = pwd_context.hash(registration.password)
        new_user = db.create_user(session, registration)
        return UserResponse(user=new_user)
      except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



##                  ##
##  Authentication  ##
##                  ##

class AccessToken(BaseModel):
    """Response model for access token."""

    access_token: str
    token_type: str
    expires_in: int
    user_id: int


def _build_access_token(user: Users) -> AccessToken:
    expiration = int(datetime.now(timezone.utc).timestamp()) + access_token_duration
    claims = Claims(sub=str(user.user_id), exp=expiration)
    access_token = jwt.encode(claims.model_dump(), key=JWT_KEY, algorithm=JWT_ALG)
    user_id = user.user_id
    return AccessToken(
        access_token=access_token,
        token_type="Bearer",
        expires_in=access_token_duration,
        user_id=user_id
    )


# Login route
@users_router.post("/token", response_model=AccessToken)
def get_access_token(
    form: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(db.get_session),
):
    """
    Get access token for user.
    """

    user = _get_authenticated_user(session, form)
    token = _build_access_token(user)
    return token


def _get_authenticated_user(
    session: Session,
    form: OAuth2PasswordRequestForm,
) -> Users:
    """
    Get an existing user from the database

    SQLModel handels input sanitization by default
    """

    user = session.exec(select(Users).where(Users.username == form.username)).first()
    if user is None or not pwd_context.verify(form.password, user.password):
        raise InvalidCredentials()

    return user


def get_current_user(session: Session = Depends(db.get_session), token: str = Depends(oauth2_scheme)) -> Users:
    """
    FastAPI dependency to get current user from bearer token
    """

    user = _decode_access_token(session, token)

    return user


def _decode_access_token(session: Session, token: str) -> Users:
    claims = Claims(**jwt.decode(token,key=JWT_KEY, algorithms=[JWT_ALG]))
    user_id = claims.sub
    return db.get_user_by_id(session, user_id)


@users_router.put("/me", response_model=UserResponse)
def update_current_user(update_data: UserUpdate, user: Users = Depends(get_current_user), session: Session = Depends(db.get_session)):
    """
    Updates Current User
    """

    if update_data.username is not None:
        user.username = update_data.username
    if update_data.first_name is not None:
        user.first_name = update_data.first_name
    if update_data.email is not None:
        user.email = update_data.email
    session.add(user)
    session.commit()
    return UserResponse(user=user)


@users_router.get(path="/xp", response_model=XpResponse)
def get_user_xp(user: Users = Depends(get_current_user), 
                session: Session = Depends(db.get_session)) -> XpResponse:
    """
    Get a user's daily and total xp
    """

    return db.get_user_xp(session=session, user=user)


@users_router.post(path="/xp/{amount}", response_model=XpResponse)
def update_user_xp(amount: int, user: Users = Depends(get_current_user), 
                   session: Session = Depends(db.get_session)) -> XpResponse:
    """
    Update a user's xp progress
    """

    return db.update_user_xp(session=session, user=user, amount=amount)


@users_router.get(path="/xp/week", response_model=DateResponse)
def get_dates_with_progress(user: Users = Depends(get_current_user), session: Session = Depends(db.get_session)) -> DateResponse:
    """
    Get the 7 most recent days a user's xp has updated 
    """

    return DateResponse(dates=db.get_xp_dates(session=session, user=user, amt=7))


@users_router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, session: Session = Depends(db.get_session)) -> UserResponse:
    """
    Get a User by user id
    """

    return UserResponse(user=db.get_user_by_id(session=session, user_id=user_id))


@users_router.put(path="/progress", response_model=ProgressResponse)
def update_user_porgress(details: ProgressUpdate, user: Users = Depends(get_current_user), 
                         session: Session = Depends(db.get_session)) -> ProgressResponse:
    """
    Update a user's unit/lesson progression
    """
    
    # Update a user's XP upon completing any lesson
    db.update_user_xp(session=session, user=user, amount=LESSON_XP_AMOUNT)
    
    return ProgressResponse(success=db.update_user_progress(session=session, user=user, details=details))


@users_router.get("/{user_id}/myfriends")
def get_friends(user_id: int,
                session: Session = Depends(db.get_session)) -> FollowersResponse:
    """
    Retrieve a lits of a user's friends
    """


    friends = db.get_followers_by_id(session=session, user_id=user_id)
    meta = {"count": len(friends)}
    return FollowersResponse(meta=meta, followers=friends)


@users_router.get("/{user_id}/permissions")
def get_user_permissions(user_id: int, session: Session = Depends(db.get_session)) -> PermissionsResponse:
    """
    Get a user's permissions level (admin or not)
    """

    user = db.get_user_by_id(session=session, user_id=user_id)
    return PermissionsResponse(is_admin=user.is_admin)


@users_router.get("/{user_id}/friends/")
async def search_friends( user_id: int, search_query: str, session: Session = Depends(db.get_session),):
    """
    Search through a user's friends for a specific friend
    """

    new_friends = db.search_for_new_friends(user_id, search_query, session)
    return new_friends


##                  ##
##    Followers     ##
##                  ##

@users_router.post("/friends/add/{user_id}", response_model=UserResponse)
def add_friend(user_id: int, 
               new_friend_id: int, 
               session: Session = Depends(db.get_session)):
      """Add New Friend"""
      add_friend = db.add_friend(user_id, new_friend_id, session)
      return UserResponse(user=add_friend)


@users_router.delete("/friends/delete/{user_id}", response_model=UserResponse)
def delete_friend(user_id: int, 
               old_friend_id: int, 
               session: Session = Depends(db.get_session)):
      """Add New Friend"""
      delete_friend = db.delete_friend(user_id, old_friend_id, session)
      return UserResponse(user=delete_friend)
       


def get_current_user(
    session: Session = Depends(db.get_session),
    token: str = Depends(oauth2_scheme),
) -> Users:
    """FastAPI dependency to get current user from bearer token."""
    user = _decode_access_token(session, token)
    return user


@users_router.put("/reset-password")
def update_user_password(password_update: PasswordUpdate,
                session: Session = Depends(db.get_session)):
    
    """Register New User"""
    try:
        hashed_password = pwd_context.hash(password_update.password)
        user = db.reset_password(session, password_update.username, hashed_password)
        return UserResponse(user=user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@users_router.put("/request-recovery/{username}")
def request_recovery(username: str, session: Session = Depends(db.get_session)):
    user = None
    try:
        user = db.get_user_by_username(session, username)
    except:
        pass

    otp = [random.randint(0, 9) for _ in range(5)]
    otp = ''.join(map(str, otp))
    send_otp_email(otp, user)
    return {"otp": otp}


def send_otp_email(otp: str, user: Users):
    try:
        if (user):
            sender = "app@gmail.com"
            password = "cabw cney iqnt souc"
            message = f"If you didn't request to reset your password, please ignore this email. Here's your one time password: {otp}."

            em = EmailMessage()
            em['From'] = sender
            em['To'] = user.email
            em['Subject'] = "Confirm Your Identity: OTP Code for Password Reset"
            em.set_content(message)

            context = ssl.create_default_context()

            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(sender, password)
                server.sendmail(sender, user.email, em.as_string())
    except:
        pass


    
class Claims(BaseModel):
    """Access token claims (aka payload)."""

    sub: str  # id of user
    exp: int  # unix timestamp


class AuthException(HTTPException):
    def __init__(self, error: str, description: str):
        super().__init__(
            status_code=401,
            detail={
                "error": error,
                "error_description": description,
            },
        )


class InvalidCredentials(AuthException):
    def __init__(self):
        super().__init__(
            error="invalid_client",
            description="invalid username or password",
        )


class InvalidToken(AuthException):
    def __init__(self):
        super().__init__(
            error="invalid_client",
            description="invalid bearer token",
        )


class ExpiredToken(AuthException):
    def __init__(self):
        super().__init__(
            error="invalid_client",
            description="expired bearer token",
        )


def _decode_access_token(session: Session, token: str) -> Users:
    try:
        claims_dict = jwt.decode(token, key=JWT_KEY, algorithms=[JWT_ALG])
        claims = Claims(**claims_dict)
        user_id = claims.sub
        user = session.get(Users, user_id)

        if user is None:
            raise InvalidToken()

        return user
    
    except:
        raise InvalidToken()
    
    