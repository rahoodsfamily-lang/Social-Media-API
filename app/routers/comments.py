from fastapi import APIRouter, HTTPException, Depends, status, Query, Header
from typing import List, Optional
from app.crud.comment_crud import CommentCRUD
from app.crud.user_crud import UserCRUD
from app.crud.post_crud import PostCRUD
from app.schemas.comment_schemas import (
    CommentCreate, CommentUpdate, CommentResponse, 
    CommentWithReplies, CommentLikeResponse
)
from app.models.user import User
from app.models.comment import Comment

router = APIRouter(prefix="/comments", tags=["comments"])

# Simplified dependency to get current user (in production, use proper JWT auth)
async def get_current_user(x_user_id: str = Header(..., description="User ID for authentication")) -> User:
    """Get current authenticated user - simplified for demo"""
    user = UserCRUD.get_user_by_uid(x_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def prepare_comment_response(comment: Comment, current_user: Optional[User] = None) -> dict:
    """Helper function to prepare comment response data"""
    author = comment.author.single()
    post = comment.post.single()
    parent_comment = comment.parent_comment.single() if hasattr(comment, 'parent_comment') else None
    
    response_data = comment.__dict__.copy()
    response_data['author_username'] = author.username if author else None
    response_data['author_uid'] = author.uid if author else None
    response_data['post_uid'] = post.uid if post else None
    response_data['parent_comment_uid'] = parent_comment.uid if parent_comment else None
    response_data['is_liked_by_user'] = False  # TODO: Check if current user liked this comment
    response_data['is_reply'] = parent_comment is not None
    
    return response_data

@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new comment"""
    try:
        comment = CommentCRUD.create_comment(current_user, comment_data)
        return prepare_comment_response(comment, current_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: str,
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get a specific comment"""
    comment = CommentCRUD.get_comment_by_uid(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Get author info
    author = comment.author.single()
    post = comment.post.single()
    parent_comment = comment.parent_comment.single()
    
    # Prepare response data
    response_data = comment.__dict__.copy()
    response_data['author_username'] = author.username if author else "Unknown"
    response_data['author_uid'] = author.uid if author else ""
    response_data['post_uid'] = post.uid if post else ""
    response_data['parent_comment_uid'] = parent_comment.uid if parent_comment else None
    response_data['is_liked_by_user'] = CommentCRUD.is_comment_liked_by_user(current_user, comment) if current_user else False
    response_data['is_reply'] = comment.is_reply
    
    return response_data

@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: str,
    comment_data: CommentUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a comment"""
    comment = CommentCRUD.get_comment_by_uid(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user is the author
    author = comment.author.single()
    if not author or author.uid != current_user.uid:
        raise HTTPException(status_code=403, detail="Not authorized to update this comment")
    
    updated_comment = CommentCRUD.update_comment(comment, comment_data)
    
    # Prepare response data
    post = updated_comment.post.single()
    parent_comment = updated_comment.parent_comment.single()
    
    response_data = updated_comment.__dict__.copy()
    response_data['author_username'] = current_user.username
    response_data['author_uid'] = current_user.uid
    response_data['post_uid'] = post.uid if post else ""
    response_data['parent_comment_uid'] = parent_comment.uid if parent_comment else None
    response_data['is_liked_by_user'] = CommentCRUD.is_comment_liked_by_user(current_user, updated_comment)
    response_data['is_reply'] = updated_comment.is_reply
    
    return response_data

@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a comment"""
    comment = CommentCRUD.get_comment_by_uid(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user is the author
    author = comment.author.single()
    if not author or author.uid != current_user.uid:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    
    CommentCRUD.delete_comment(comment)

@router.post("/{comment_id}/like", response_model=CommentLikeResponse)
async def like_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Like a comment"""
    comment = CommentCRUD.get_comment_by_uid(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    success = CommentCRUD.like_comment(current_user, comment)
    if success:
        return CommentLikeResponse(
            message="Comment liked successfully",
            is_liked=True,
            likes_count=comment.likes_count
        )
    else:
        return CommentLikeResponse(
            message="Comment already liked",
            is_liked=True,
            likes_count=comment.likes_count
        )

@router.delete("/{comment_id}/like", response_model=CommentLikeResponse)
async def unlike_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Unlike a comment"""
    comment = CommentCRUD.get_comment_by_uid(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    success = CommentCRUD.unlike_comment(current_user, comment)
    if success:
        return CommentLikeResponse(
            message="Comment unliked successfully",
            is_liked=False,
            likes_count=comment.likes_count
        )
    else:
        return CommentLikeResponse(
            message="Comment was not liked",
            is_liked=False,
            likes_count=comment.likes_count
        )

@router.get("/post/{post_id}", response_model=List[CommentWithReplies])
async def get_post_comments(
    post_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Get comments for a specific post"""
    post = PostCRUD.get_post_by_uid(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    comments = CommentCRUD.get_post_comments(post, skip, limit)
    
    # Convert to response format with replies
    comments_with_replies = []
    for comment in comments:
        author = comment.author.single()
        
        # Get replies
        replies = CommentCRUD.get_comment_replies(comment, 0, 5)  # Limit replies for performance
        reply_responses = []
        
        for reply in replies:
            reply_author = reply.author.single()
            reply_response = CommentResponse(
                uid=reply.uid,
                content=reply.content,
                mentions=reply.mentions,
                author_username=reply_author.username if reply_author else "Unknown",
                author_uid=reply_author.uid if reply_author else "",
                post_uid=post_id,
                parent_comment_uid=comment.uid,
                likes_count=reply.likes_count,
                replies_count=reply.replies_count,
                created_at=reply.created_at,
                updated_at=reply.updated_at,
                is_edited=reply.is_edited,
                is_pinned=reply.is_pinned,
                image_url=reply.image_url,
                gif_url=reply.gif_url,
                is_liked_by_user=CommentCRUD.is_comment_liked_by_user(current_user, reply) if current_user else False,
                is_reply=True
            )
            reply_responses.append(reply_response)
        
        comment_with_replies = CommentWithReplies(
            uid=comment.uid,
            content=comment.content,
            mentions=comment.mentions,
            author_username=author.username if author else "Unknown",
            author_uid=author.uid if author else "",
            post_uid=post_id,
            parent_comment_uid=None,
            likes_count=comment.likes_count,
            replies_count=comment.replies_count,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            is_edited=comment.is_edited,
            is_pinned=comment.is_pinned,
            image_url=comment.image_url,
            gif_url=comment.gif_url,
            is_liked_by_user=CommentCRUD.is_comment_liked_by_user(current_user, comment) if current_user else False,
            is_reply=False,
            replies=reply_responses
        )
        comments_with_replies.append(comment_with_replies)
    
    return comments_with_replies

@router.get("/{comment_id}/replies", response_model=List[CommentResponse])
async def get_comment_replies(
    comment_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50)
):
    """Get replies to a specific comment"""
    comment = CommentCRUD.get_comment_by_uid(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    replies = CommentCRUD.get_comment_replies(comment, skip, limit)
    
    # Convert to response format
    reply_responses = []
    for reply in replies:
        author = reply.author.single()
        post = reply.post.single()
        
        reply_response = CommentResponse(
            uid=reply.uid,
            content=reply.content,
            mentions=reply.mentions,
            author_username=author.username if author else "Unknown",
            author_uid=author.uid if author else "",
            post_uid=post.uid if post else "",
            parent_comment_uid=comment_id,
            likes_count=reply.likes_count,
            replies_count=reply.replies_count,
            created_at=reply.created_at,
            updated_at=reply.updated_at,
            is_edited=reply.is_edited,
            is_pinned=reply.is_pinned,
            image_url=reply.image_url,
            gif_url=reply.gif_url,
            is_liked_by_user=CommentCRUD.is_comment_liked_by_user(current_user, reply) if current_user else False,
            is_reply=True
        )
        reply_responses.append(reply_response)
    
    return reply_responses

@router.get("/user/{user_id}", response_model=List[CommentResponse])
async def get_user_comments(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Get comments by a specific user"""
    user = UserCRUD.get_user_by_uid(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    comments = CommentCRUD.get_user_comments(user, skip, limit)
    
    # Convert to response format
    comment_responses = []
    for comment in comments:
        post = comment.post.single()
        parent_comment = comment.parent_comment.single()
        
        comment_response = CommentResponse(
            uid=comment.uid,
            content=comment.content,
            mentions=comment.mentions,
            author_username=user.username,
            author_uid=user.uid,
            post_uid=post.uid if post else "",
            parent_comment_uid=parent_comment.uid if parent_comment else None,
            likes_count=comment.likes_count,
            replies_count=comment.replies_count,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            is_edited=comment.is_edited,
            is_pinned=comment.is_pinned,
            image_url=comment.image_url,
            gif_url=comment.gif_url,
            is_liked_by_user=False,  # Not checking for current user context
            is_reply=comment.is_reply
        )
        comment_responses.append(comment_response)
    
    return comment_responses

@router.post("/{comment_id}/pin")
async def pin_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Pin a comment"""
    comment = CommentCRUD.get_comment_by_uid(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user is the author of the post or comment
    comment_author = comment.author.single()
    post = comment.post.single()
    post_author = post.author.single() if post else None
    
    if (not comment_author or comment_author.uid != current_user.uid) and \
       (not post_author or post_author.uid != current_user.uid):
        raise HTTPException(status_code=403, detail="Not authorized to pin this comment")
    
    CommentCRUD.pin_comment(comment)
    return {"message": "Comment pinned successfully"}

@router.delete("/{comment_id}/pin")
async def unpin_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Unpin a comment"""
    comment = CommentCRUD.get_comment_by_uid(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user is the author of the post or comment
    comment_author = comment.author.single()
    post = comment.post.single()
    post_author = post.author.single() if post else None
    
    if (not comment_author or comment_author.uid != current_user.uid) and \
       (not post_author or post_author.uid != current_user.uid):
        raise HTTPException(status_code=403, detail="Not authorized to unpin this comment")
    
    CommentCRUD.unpin_comment(comment)
    return {"message": "Comment unpinned successfully"}
