from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
    mentions: List[str] = []

class CommentCreate(CommentBase):
    post_uid: str
    parent_comment_uid: Optional[str] = None  # For replies
    image_url: Optional[str] = None
    gif_url: Optional[str] = None
    
    @validator('mentions')
    def validate_mentions(cls, v):
        return [mention.lower().replace('@', '') for mention in v if mention.strip()]

class CommentUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=1000)
    mentions: Optional[List[str]] = None
    
    @validator('mentions')
    def validate_mentions(cls, v):
        if v is not None:
            return [mention.lower().replace('@', '') for mention in v if mention.strip()]
        return v

class CommentResponse(CommentBase):
    uid: str
    author_username: str
    author_uid: str
    post_uid: str
    parent_comment_uid: Optional[str]
    likes_count: int
    replies_count: int
    created_at: datetime
    updated_at: datetime
    is_edited: bool
    is_pinned: bool
    image_url: Optional[str]
    gif_url: Optional[str]
    is_liked_by_user: bool = False
    is_reply: bool = False
    
    class Config:
        from_attributes = True

class CommentWithReplies(CommentResponse):
    replies: List[CommentResponse] = []

class CommentLikeResponse(BaseModel):
    message: str
    is_liked: bool
    likes_count: int
