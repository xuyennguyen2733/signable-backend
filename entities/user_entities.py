from datetime import  datetime, date

from pydantic import BaseModel
from sqlmodel import SQLModel
from typing import Optional

from entities.resource_entities import Metadata

##                  ##
##      Models      ##
##                  ##

class UserRegistration(SQLModel):
    """Request model to register new user."""

    username: str
    email: str
    first_name: str
    last_name: str
    password: str


class PasswordUpdate(SQLModel):
    """Request model to update password"""

    username: str
    password: str


class UserModel(SQLModel):
    """ 
    API definition of a User
    """
    user_id: int
    username: str
    first_name: str
    last_name: str
    email: str
    created_at: datetime
    unit_progress: int
    lesson_index: int
    days_logged: int


class FriendModel(SQLModel):
    """
    API definition of a Friend relationship
    """

    follower_id: int
    followed_id: int


##                     ##
##      Responses      ##
##                     ##

class UserResponse(BaseModel):
    """ 
    API response for an individual User 
    """
    
    user: UserModel


class ProgressResponse(BaseModel):
    """
    API Response when a user's progress is updated
    """

    success: bool


class XpResponse(BaseModel):
    """
    API Response when a user's xp is updated
    """

    user_id: int
    daily_xp: int
    total_xp: int


class DateResponse(BaseModel):
    """
    API Response containing a range of dates
    """

    dates: list[date]


class PermissionsResponse(BaseModel):
    """
    API response for a user's permissions level
    """

    is_admin: bool


class UserUpdate(SQLModel):
    """
    
    """

    first_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None


class ProgressUpdate(BaseModel):
    """
    Request model for updating a user's unit/lesson progress
    in the cirriculum
    """
    
    unit_progress: Optional[int] = None
    lesson_index: Optional[int] = None


class FollowersResponse(BaseModel):
    """
    API response for all followers of a User
    """

    meta: Metadata
    followers: list[UserModel]


class FollowingResponse(BaseModel):
    """
    API resopnse for all Users a User is following
    """

    meta: Metadata
    followers: list[UserModel]


##                      ##
##      Collections     ##
##                      ##

class UserCollection(BaseModel):
    """ 
    API response for a multiple Users 
    """

    meta: Metadata
    users: list[UserModel]


class FriendsCollection(BaseModel):
    """
    API response for a user's followers
    """

    meta: Metadata
    followers: list[FriendModel]

