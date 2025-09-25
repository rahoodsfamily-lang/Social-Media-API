from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    like = "like"
    comment = "comment"
    follow = "follow"
    mention = "mention"
    share = "share"
    group_invite = "group_invite"
    group_request = "group_request"
    post_approved = "post_approved"
    friend_request = "friend_request"
    birthday = "birthday"
    system = "system"

class NotificationBase(BaseModel):
    title: str = Field(..., max_length=200)
    message: str = Field(..., max_length=500)
    notification_type: NotificationType
    action_url: Optional[str] = None
    metadata: Dict[str, Any] = {}

class NotificationCreate(NotificationBase):
    recipient_uid: str
    sender_uid: Optional[str] = None
    related_post_uid: Optional[str] = None
    related_comment_uid: Optional[str] = None
    related_group_uid: Optional[str] = None

class NotificationResponse(NotificationBase):
    uid: str
    recipient_uid: str
    sender_uid: Optional[str]
    sender_username: Optional[str]
    is_read: bool
    is_seen: bool
    created_at: datetime
    read_at: Optional[datetime]
    related_post_uid: Optional[str]
    related_comment_uid: Optional[str]
    related_group_uid: Optional[str]
    
    class Config:
        from_attributes = True

class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None
    is_seen: Optional[bool] = None

class NotificationStats(BaseModel):
    total_count: int
    unread_count: int
    unseen_count: int
    by_type: Dict[str, int] = {}

class BulkNotificationUpdate(BaseModel):
    notification_uids: List[str]
    mark_as_read: Optional[bool] = None
    mark_as_seen: Optional[bool] = None
