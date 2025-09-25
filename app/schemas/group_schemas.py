from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class GroupType(str, Enum):
    public = "public"
    private = "private"
    secret = "secret"

class GroupBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    group_type: GroupType = GroupType.public
    category: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = None
    allow_member_posts: bool = True
    require_approval: bool = False
    tags: List[str] = []
    rules: List[str] = []
    guidelines: Optional[str] = Field(None, max_length=2000)

class GroupCreate(GroupBase):
    @validator('tags')
    def validate_tags(cls, v):
        return [tag.lower().strip() for tag in v if tag.strip()]

class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    group_type: Optional[GroupType] = None
    category: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = None
    allow_member_posts: Optional[bool] = None
    require_approval: Optional[bool] = None
    tags: Optional[List[str]] = None
    rules: Optional[List[str]] = None
    guidelines: Optional[str] = Field(None, max_length=2000)
    profile_picture_url: Optional[str] = None
    cover_photo_url: Optional[str] = None
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            return [tag.lower().strip() for tag in v if tag.strip()]
        return v

class GroupResponse(GroupBase):
    uid: str
    owner_username: str
    owner_uid: str
    members_count: int
    posts_count: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    profile_picture_url: Optional[str]
    cover_photo_url: Optional[str]
    user_role: Optional[str] = None  # owner, admin, moderator, member, or None
    is_member: bool = False
    
    class Config:
        from_attributes = True

class GroupSummary(BaseModel):
    uid: str
    name: str
    description: Optional[str]
    group_type: GroupType
    category: Optional[str]
    members_count: int
    profile_picture_url: Optional[str]
    
    class Config:
        from_attributes = True

class GroupMemberResponse(BaseModel):
    uid: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    profile_picture_url: Optional[str]
    role: str  # owner, admin, moderator, member
    joined_at: datetime
    
    class Config:
        from_attributes = True

class GroupJoinRequest(BaseModel):
    message: Optional[str] = Field(None, max_length=500)

class GroupInviteCreate(BaseModel):
    username: str
    message: Optional[str] = Field(None, max_length=500)

class GroupRoleUpdate(BaseModel):
    username: str
    role: str = Field(..., pattern="^(admin|moderator|member)$")

class GroupMembershipResponse(BaseModel):
    message: str
    is_member: bool
    members_count: int
