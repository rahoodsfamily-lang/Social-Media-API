from fastapi import APIRouter, HTTPException, Depends, status, Query, Header
from typing import List, Optional
from app.crud.post_crud import PostCRUD
from app.crud.user_crud import UserCRUD
from app.schemas.post_schemas import (
    PostCreate, PostUpdate, PostResponse, PostSummary, 
    LikeResponse, SharePostCreate
)
from app.models.user import User
from app.models.post import Post

router = APIRouter(prefix="/posts", tags=["posts"])

# Simplified dependency to get current user (in production, use proper JWT auth)
async def get_current_user(x_user_id: str = Header(..., description="User ID for authentication")) -> User:
    """Get current authenticated user - simplified for demo"""
    user = UserCRUD.get_user_by_uid(x_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new post"""
    try:
        post = PostCRUD.create_post(current_user, post_data)
        # Add additional fields for response
        response_data = post.__dict__.copy()
        response_data['author_username'] = current_user.username
        response_data['author_uid'] = current_user.uid
        response_data['is_liked_by_user'] = False
        return response_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str,
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get a specific post"""
    post = PostCRUD.get_post_by_uid(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Get author info
    author = post.author.single()
    
    # Prepare response data
    response_data = post.__dict__.copy()
    response_data['author_username'] = author.username if author else "Unknown"
    response_data['author_uid'] = author.uid if author else ""
    response_data['is_liked_by_user'] = PostCRUD.is_post_liked_by_user(current_user, post) if current_user else False
    
    return response_data

@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: str,
    post_data: PostUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a post"""
    post = PostCRUD.get_post_by_uid(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if user is the author
    author = post.author.single()
    if not author or author.uid != current_user.uid:
        raise HTTPException(status_code=403, detail="Not authorized to update this post")
    
    updated_post = PostCRUD.update_post(post, post_data)
    
    # Prepare response data
    response_data = updated_post.__dict__.copy()
    response_data['author_username'] = current_user.username
    response_data['author_uid'] = current_user.uid
    response_data['is_liked_by_user'] = PostCRUD.is_post_liked_by_user(current_user, updated_post)
    
    return response_data

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a post"""
    post = PostCRUD.get_post_by_uid(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if user is the author
    author = post.author.single()
    if not author or author.uid != current_user.uid:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")
    
    PostCRUD.delete_post(post)

@router.post("/{post_id}/like", response_model=LikeResponse)
async def like_post(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    """Like a post"""
    post = PostCRUD.get_post_by_uid(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    success = PostCRUD.like_post(current_user, post)
    if success:
        return LikeResponse(
            message="Post liked successfully",
            is_liked=True,
            likes_count=post.likes_count
        )
    else:
        return LikeResponse(
            message="Post already liked",
            is_liked=True,
            likes_count=post.likes_count
        )

@router.delete("/{post_id}/like", response_model=LikeResponse)
async def unlike_post(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    """Unlike a post"""
    post = PostCRUD.get_post_by_uid(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    success = PostCRUD.unlike_post(current_user, post)
    if success:
        return LikeResponse(
            message="Post unliked successfully",
            is_liked=False,
            likes_count=post.likes_count
        )
    else:
        return LikeResponse(
            message="Post was not liked",
            is_liked=False,
            likes_count=post.likes_count
        )

@router.post("/{post_id}/share", response_model=PostResponse)
async def share_post(
    post_id: str,
    share_data: SharePostCreate,
    current_user: User = Depends(get_current_user)
):
    """Share/repost a post"""
    original_post = PostCRUD.get_post_by_uid(share_data.original_post_uid)
    if not original_post:
        raise HTTPException(status_code=404, detail="Original post not found")
    
    shared_post = PostCRUD.share_post(current_user, original_post, share_data.content)
    
    # Prepare response data
    response_data = shared_post.__dict__.copy()
    response_data['author_username'] = current_user.username
    response_data['author_uid'] = current_user.uid
    response_data['is_liked_by_user'] = False
    
    return response_data

@router.get("/", response_model=List[PostSummary])
async def get_public_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Get public posts for explore/discover"""
    posts = PostCRUD.get_public_posts(skip, limit)
    
    # Convert to summary format
    summaries = []
    for post in posts:
        author = post.author.single()
        summary = PostSummary(
            uid=post.uid,
            content=post.content[:100] + "..." if len(post.content) > 100 else post.content,
            author_username=author.username if author else "Unknown",
            likes_count=post.likes_count,
            comments_count=post.comments_count,
            created_at=post.created_at,
            post_type=post.post_type
        )
        summaries.append(summary)
    
    return summaries

@router.get("/trending", response_model=List[PostSummary])
async def get_trending_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Get trending posts"""
    posts = PostCRUD.get_trending_posts(skip, limit)
    
    # Convert to summary format
    summaries = []
    for post in posts:
        author = post.author.single()
        summary = PostSummary(
            uid=post.uid,
            content=post.content[:100] + "..." if len(post.content) > 100 else post.content,
            author_username=author.username if author else "Unknown",
            likes_count=post.likes_count,
            comments_count=post.comments_count,
            created_at=post.created_at,
            post_type=post.post_type
        )
        summaries.append(summary)
    
    return summaries

@router.get("/feed/", response_model=List[PostSummary])
async def get_user_feed(
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Get personalized feed for current user"""
    posts = PostCRUD.get_feed_posts(current_user, skip, limit)
    
    # Convert to summary format
    summaries = []
    for post in posts:
        author = post.author.single()
        summary = PostSummary(
            uid=post.uid,
            content=post.content[:100] + "..." if len(post.content) > 100 else post.content,
            author_username=author.username if author else "Unknown",
            likes_count=post.likes_count,
            comments_count=post.comments_count,
            created_at=post.created_at,
            post_type=post.post_type
        )
        summaries.append(summary)
    
    return summaries

@router.get("/user/{user_id}", response_model=List[PostSummary])
async def get_user_posts(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Get posts by a specific user"""
    user = UserCRUD.get_user_by_uid(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    posts = PostCRUD.get_user_posts(user, skip, limit)
    
    # Convert to summary format
    summaries = []
    for post in posts:
        summary = PostSummary(
            uid=post.uid,
            content=post.content[:100] + "..." if len(post.content) > 100 else post.content,
            author_username=user.username,
            likes_count=post.likes_count,
            comments_count=post.comments_count,
            created_at=post.created_at,
            post_type=post.post_type
        )
        summaries.append(summary)
    
    return summaries

@router.get("/search/", response_model=List[PostSummary])
async def search_posts(
    q: str = Query(..., min_length=2),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Search posts"""
    posts = PostCRUD.search_posts(q, skip, limit)
    
    # Convert to summary format
    summaries = []
    for post in posts:
        author = post.author.single()
        summary = PostSummary(
            uid=post.uid,
            content=post.content[:100] + "..." if len(post.content) > 100 else post.content,
            author_username=author.username if author else "Unknown",
            likes_count=post.likes_count,
            comments_count=post.comments_count,
            created_at=post.created_at,
            post_type=post.post_type
        )
        summaries.append(summary)
    
    return summaries

@router.get("/hashtag/{hashtag}", response_model=List[PostSummary])
async def get_posts_by_hashtag(
    hashtag: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Get posts by hashtag"""
    posts = PostCRUD.get_posts_by_hashtag(hashtag, skip, limit)
    
    # Convert to summary format
    summaries = []
    for post in posts:
        author = post.author.single()
        summary = PostSummary(
            uid=post.uid,
            content=post.content[:100] + "..." if len(post.content) > 100 else post.content,
            author_username=author.username if author else "Unknown",
            likes_count=post.likes_count,
            comments_count=post.comments_count,
            created_at=post.created_at,
            post_type=post.post_type
        )
        summaries.append(summary)
    
    return summaries

@router.post("/{post_id}/pin")
async def pin_post(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    """Pin a post"""
    post = PostCRUD.get_post_by_uid(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if user is the author
    author = post.author.single()
    if not author or author.uid != current_user.uid:
        raise HTTPException(status_code=403, detail="Not authorized to pin this post")
    
    PostCRUD.pin_post(post)
    return {"message": "Post pinned successfully"}

@router.delete("/{post_id}/pin")
async def unpin_post(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    """Unpin a post"""
    post = PostCRUD.get_post_by_uid(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if user is the author
    author = post.author.single()
    if not author or author.uid != current_user.uid:
        raise HTTPException(status_code=403, detail="Not authorized to unpin this post")
    
    PostCRUD.unpin_post(post)
    return {"message": "Post unpinned successfully"}
