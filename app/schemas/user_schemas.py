from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    bio: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = None
    phone_number: Optional[str] = None
    is_private: bool = False
    interests: List[str] = []

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    bio: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = None
    phone_number: Optional[str] = None
    is_private: Optional[bool] = None
    interests: Optional[List[str]] = None
    profile_picture_url: Optional[str] = None
    cover_photo_url: Optional[str] = None

class UserResponse(UserBase):
    uid: str
    is_active: bool
    is_verified: bool
    followers_count: int
    following_count: int
    posts_count: int
    created_at: datetime
    last_login: Optional[datetime]
    profile_picture_url: Optional[str]
    cover_photo_url: Optional[str]
    
    class Config:
        from_attributes = True

class UserPublic(BaseModel):
    uid: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    bio: Optional[str]
    location: Optional[str]
    website: Optional[str]
    is_verified: bool
    followers_count: int
    following_count: int
    posts_count: int
    profile_picture_url: Optional[str]
    cover_photo_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username_or_email: str
    password: str

class UserPasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_new_password: str
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('New passwords do not match')
        return v

class FollowResponse(BaseModel):
    message: str
    is_following: bool
    followers_count: int
    following_count: int
