from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PostType(str, Enum):
    text = "text"
    image = "image"
    video = "video"
    link = "link"
    poll = "poll"

class PostVisibility(str, Enum):
    public = "public"
    friends = "friends"
    private = "private"

class PostBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    title: Optional[str] = Field(None, max_length=200)
    post_type: PostType = PostType.text
    visibility: PostVisibility = PostVisibility.public
    location: Optional[str] = None
    allow_comments: bool = True
    hashtags: List[str] = []
    mentions: List[str] = []

class PostCreate(PostBase):
    image_urls: List[str] = []
    video_urls: List[str] = []
    
    @validator('hashtags')
    def validate_hashtags(cls, v):
        return [tag.lower().replace('#', '') for tag in v if tag.strip()]
    
    @validator('mentions')
    def validate_mentions(cls, v):
        return [mention.lower().replace('@', '') for mention in v if mention.strip()]

class PostUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=2000)
    title: Optional[str] = Field(None, max_length=200)
    visibility: Optional[PostVisibility] = None
    location: Optional[str] = None
    allow_comments: Optional[bool] = None
    hashtags: Optional[List[str]] = None
    mentions: Optional[List[str]] = None
    
    @validator('hashtags')
    def validate_hashtags(cls, v):
        if v is not None:
            return [tag.lower().replace('#', '') for tag in v if tag.strip()]
        return v
    
    @validator('mentions')
    def validate_mentions(cls, v):
        if v is not None:
            return [mention.lower().replace('@', '') for mention in v if mention.strip()]
        return v

class PostResponse(PostBase):
    uid: str
    author_username: str
    author_uid: str
    likes_count: int
    comments_count: int
    shares_count: int
    views_count: int
    created_at: datetime
    updated_at: datetime
    is_pinned: bool
    is_archived: bool
    image_urls: List[str]
    video_urls: List[str]
    is_liked_by_user: bool = False
    
    class Config:
        from_attributes = True

class PostSummary(BaseModel):
    uid: str
    content: str = Field(..., max_length=100)  # Truncated content
    author_username: str
    likes_count: int
    comments_count: int
    created_at: datetime
    post_type: PostType
    
    class Config:
        from_attributes = True

class LikeResponse(BaseModel):
    message: str
    is_liked: bool
    likes_count: int

class SharePostCreate(BaseModel):
    original_post_uid: str
    content: Optional[str] = Field(None, max_length=500)  # Optional comment when sharing
