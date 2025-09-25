from fastapi import APIRouter, HTTPException, Depends, status, Header, Query
from typing import List, Optional
from app.crud.user_crud import UserCRUD
from app.schemas.user_schemas import (
    UserCreate, UserUpdate, UserResponse, UserPublic, 
    UserLogin, UserPasswordChange, FollowResponse
)
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])

# Simplified dependency to get current user (in production, use proper JWT auth)
async def get_current_user(x_user_id: str = Header(..., description="User ID for authentication")) -> User:
    """Get current authenticated user - simplified for demo"""
    user = UserCRUD.get_user_by_uid(x_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        user = UserCRUD.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=UserResponse)
async def login_user(login_data: UserLogin):
    """Authenticate user login"""
    user = UserCRUD.authenticate_user(login_data.username_or_email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    return user

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile"""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update current user's profile"""
    updated_user = UserCRUD.update_user(current_user, user_data)
    return updated_user

@router.post("/change-password")
async def change_password(
    password_data: UserPasswordChange,
    current_user: User = Depends(get_current_user)
):
    """Change user password"""
    success = UserCRUD.change_password(
        current_user, 
        password_data.current_password, 
        password_data.new_password
    )
    if not success:
        raise HTTPException(status_code=400, detail="Invalid current password")
    return {"message": "Password changed successfully"}

@router.get("/{user_id}", response_model=UserPublic)
async def get_user_profile(user_id: str):
    """Get user profile by ID"""
    user = UserCRUD.get_user_by_uid(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/username/{username}", response_model=UserPublic)
async def get_user_by_username(username: str):
    """Get user profile by username"""
    user = UserCRUD.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/{user_id}/follow", response_model=FollowResponse)
async def follow_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Follow a user"""
    target_user = UserCRUD.get_user_by_uid(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        success = UserCRUD.follow_user(current_user, target_user)
        if success:
            return FollowResponse(
                message=f"You are now following {target_user.username}",
                is_following=True,
                followers_count=target_user.followers_count,
                following_count=current_user.following_count
            )
        else:
            return FollowResponse(
                message=f"You are already following {target_user.username}",
                is_following=True,
                followers_count=target_user.followers_count,
                following_count=current_user.following_count
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{user_id}/follow", response_model=FollowResponse)
async def unfollow_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Unfollow a user"""
    target_user = UserCRUD.get_user_by_uid(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    success = UserCRUD.unfollow_user(current_user, target_user)
    if success:
        return FollowResponse(
            message=f"You unfollowed {target_user.username}",
            is_following=False,
            followers_count=target_user.followers_count,
            following_count=current_user.following_count
        )
    else:
        return FollowResponse(
            message=f"You are not following {target_user.username}",
            is_following=False,
            followers_count=target_user.followers_count,
            following_count=current_user.following_count
        )

@router.get("/{user_id}/followers", response_model=List[UserPublic])
async def get_user_followers(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Get user's followers"""
    user = UserCRUD.get_user_by_uid(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    followers = UserCRUD.get_followers(user, skip, limit)
    return followers

@router.get("/{user_id}/following", response_model=List[UserPublic])
async def get_user_following(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Get users that the user is following"""
    user = UserCRUD.get_user_by_uid(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    following = UserCRUD.get_following(user, skip, limit)
    return following

@router.get("/search/", response_model=List[UserPublic])
async def search_users(
    q: str = Query(..., min_length=2),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Search users"""
    users = UserCRUD.search_users(q, skip, limit)
    return users

@router.get("/me/suggestions", response_model=List[UserPublic])
async def get_user_suggestions(
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50)
):
    """Get user suggestions for current user"""
    suggestions = UserCRUD.get_user_suggestions(current_user, limit)
    return suggestions

@router.post("/me/deactivate")
async def deactivate_account(current_user: User = Depends(get_current_user)):
    """Deactivate user account"""
    UserCRUD.deactivate_user(current_user)
    return {"message": "Account deactivated successfully"}

@router.post("/me/activate")
async def activate_account(current_user: User = Depends(get_current_user)):
    """Activate user account"""
    UserCRUD.activate_user(current_user)
    return {"message": "Account activated successfully"}
