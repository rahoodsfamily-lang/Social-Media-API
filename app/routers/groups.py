from fastapi import APIRouter, HTTPException, Depends, status, Query, Header
from typing import List, Optional
from app.crud.group_crud import GroupCRUD
from app.crud.user_crud import UserCRUD
from app.schemas.group_schemas import (
    GroupCreate, GroupUpdate, GroupResponse, GroupSummary,
    GroupMemberResponse, GroupJoinRequest, GroupInviteCreate,
    GroupRoleUpdate, GroupMembershipResponse
)
from app.models.user import User
from app.models.group import Group

router = APIRouter(prefix="/groups", tags=["groups"])

# Simplified dependency to get current user (in production, use proper JWT auth)
async def get_current_user(x_user_id: str = Header(..., description="User ID for authentication")) -> User:
    """Get current authenticated user - simplified for demo"""
    user = UserCRUD.get_user_by_uid(x_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new group"""
    try:
        group = GroupCRUD.create_group(current_user, group_data)
        
        # Prepare response data
        response_data = group.__dict__.copy()
        response_data['owner_username'] = current_user.username
        response_data['owner_uid'] = current_user.uid
        response_data['user_role'] = 'owner'
        response_data['is_member'] = True
        
        return response_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: str,
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get a specific group"""
    group = GroupCRUD.get_group_by_uid(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Get owner info
    owner = group.owner.single()
    
    # Determine user role and membership
    user_role = None
    is_member = False
    if current_user:
        if group.owner.is_connected(current_user):
            user_role = 'owner'
            is_member = True
        elif group.admins.is_connected(current_user):
            user_role = 'admin'
            is_member = True
        elif group.moderators.is_connected(current_user):
            user_role = 'moderator'
            is_member = True
        elif group.is_member(current_user):
            user_role = 'member'
            is_member = True
    
    # Prepare response data
    response_data = group.__dict__.copy()
    response_data['owner_username'] = owner.username if owner else "Unknown"
    response_data['owner_uid'] = owner.uid if owner else ""
    response_data['user_role'] = user_role
    response_data['is_member'] = is_member
    
    return response_data

@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: str,
    group_data: GroupUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a group"""
    group = GroupCRUD.get_group_by_uid(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check if user is admin or owner
    if not group.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Not authorized to update this group")
    
    updated_group = GroupCRUD.update_group(group, group_data)
    
    # Prepare response data
    owner = updated_group.owner.single()
    user_role = 'owner' if group.owner.is_connected(current_user) else 'admin'
    
    response_data = updated_group.__dict__.copy()
    response_data['owner_username'] = owner.username if owner else "Unknown"
    response_data['owner_uid'] = owner.uid if owner else ""
    response_data['user_role'] = user_role
    response_data['is_member'] = True
    
    return response_data

@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a group"""
    group = GroupCRUD.get_group_by_uid(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check if user is the owner
    if not group.owner.is_connected(current_user):
        raise HTTPException(status_code=403, detail="Only the owner can delete the group")
    
    GroupCRUD.delete_group(group)

@router.post("/{group_id}/join", response_model=GroupMembershipResponse)
async def join_group(
    group_id: str,
    join_request: Optional[GroupJoinRequest] = None,
    current_user: User = Depends(get_current_user)
):
    """Join a group"""
    group = GroupCRUD.get_group_by_uid(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    try:
        success = GroupCRUD.join_group(current_user, group)
        if success:
            return GroupMembershipResponse(
                message=f"Successfully joined {group.name}",
                is_member=True,
                members_count=group.members_count
            )
        else:
            return GroupMembershipResponse(
                message=f"Join request sent for {group.name}. Waiting for approval.",
                is_member=False,
                members_count=group.members_count
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{group_id}/join", response_model=GroupMembershipResponse)
async def leave_group(
    group_id: str,
    current_user: User = Depends(get_current_user)
):
    """Leave a group"""
    group = GroupCRUD.get_group_by_uid(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    try:
        success = GroupCRUD.leave_group(current_user, group)
        if success:
            return GroupMembershipResponse(
                message=f"Successfully left {group.name}",
                is_member=False,
                members_count=group.members_count
            )
        else:
            return GroupMembershipResponse(
                message=f"You are not a member of {group.name}",
                is_member=False,
                members_count=group.members_count
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{group_id}/approve/{user_id}")
async def approve_join_request(
    group_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Approve a join request"""
    group = GroupCRUD.get_group_by_uid(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    user = UserCRUD.get_user_by_uid(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        success = GroupCRUD.approve_join_request(group, user, current_user)
        if success:
            return {"message": f"Approved {user.username}'s join request"}
        else:
            return {"message": f"No pending request from {user.username}"}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.delete("/{group_id}/approve/{user_id}")
async def reject_join_request(
    group_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Reject a join request"""
    group = GroupCRUD.get_group_by_uid(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    user = UserCRUD.get_user_by_uid(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        success = GroupCRUD.reject_join_request(group, user, current_user)
        if success:
            return {"message": f"Rejected {user.username}'s join request"}
        else:
            return {"message": f"No pending request from {user.username}"}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.post("/{group_id}/promote")
async def promote_member(
    group_id: str,
    role_update: GroupRoleUpdate,
    current_user: User = Depends(get_current_user)
):
    """Promote a member to admin or moderator"""
    group = GroupCRUD.get_group_by_uid(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    user = UserCRUD.get_user_by_username(role_update.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        success = GroupCRUD.promote_member(group, user, role_update.role, current_user)
        if success:
            return {"message": f"Promoted {user.username} to {role_update.role}"}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.delete("/{group_id}/promote/{user_id}")
async def demote_member(
    group_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Demote a member from admin or moderator"""
    group = GroupCRUD.get_group_by_uid(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    user = UserCRUD.get_user_by_uid(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        success = GroupCRUD.demote_member(group, user, current_user)
        if success:
            return {"message": f"Demoted {user.username} to regular member"}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.delete("/{group_id}/members/{user_id}")
async def remove_member(
    group_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove a member from the group"""
    group = GroupCRUD.get_group_by_uid(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    user = UserCRUD.get_user_by_uid(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        success = GroupCRUD.remove_member(group, user, current_user)
        if success:
            return {"message": f"Removed {user.username} from the group"}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.get("/{group_id}/members", response_model=List[GroupMemberResponse])
async def get_group_members(
    group_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Get group members"""
    group = GroupCRUD.get_group_by_uid(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    members = GroupCRUD.get_group_members(group, skip, limit)
    
    # Convert to response format with roles
    member_responses = []
    for member in members:
        # Determine role
        if group.owner.is_connected(member):
            role = 'owner'
        elif group.admins.is_connected(member):
            role = 'admin'
        elif group.moderators.is_connected(member):
            role = 'moderator'
        else:
            role = 'member'
        
        member_response = GroupMemberResponse(
            uid=member.uid,
            username=member.username,
            first_name=member.first_name,
            last_name=member.last_name,
            profile_picture_url=member.profile_picture_url,
            role=role,
            joined_at=member.created_at  # Simplified - would need join date
        )
        member_responses.append(member_response)
    
    return member_responses

@router.get("/{group_id}/pending", response_model=List[GroupMemberResponse])
async def get_pending_requests(
    group_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get pending join requests for a group"""
    group = GroupCRUD.get_group_by_uid(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check if user is admin or owner
    if not group.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Not authorized to view pending requests")
    
    pending_users = GroupCRUD.get_pending_requests(group)
    
    # Convert to response format
    pending_responses = []
    for user in pending_users:
        pending_response = GroupMemberResponse(
            uid=user.uid,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            profile_picture_url=user.profile_picture_url,
            role='pending',
            joined_at=user.created_at  # Simplified
        )
        pending_responses.append(pending_response)
    
    return pending_responses

@router.get("/", response_model=List[GroupSummary])
async def get_public_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Get public groups"""
    groups = GroupCRUD.get_public_groups(skip, limit)
    
    # Convert to summary format
    summaries = []
    for group in groups:
        summary = GroupSummary(
            uid=group.uid,
            name=group.name,
            description=group.description,
            group_type=group.group_type,
            category=group.category,
            members_count=group.members_count,
            profile_picture_url=group.profile_picture_url
        )
        summaries.append(summary)
    
    return summaries

@router.get("/search/", response_model=List[GroupSummary])
async def search_groups(
    q: str = Query(..., min_length=2),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Search groups"""
    groups = GroupCRUD.search_groups(q, skip, limit)
    
    # Convert to summary format
    summaries = []
    for group in groups:
        summary = GroupSummary(
            uid=group.uid,
            name=group.name,
            description=group.description,
            group_type=group.group_type,
            category=group.category,
            members_count=group.members_count,
            profile_picture_url=group.profile_picture_url
        )
        summaries.append(summary)
    
    return summaries

@router.get("/user/{user_id}", response_model=List[GroupSummary])
async def get_user_groups(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Get groups that user is a member of"""
    user = UserCRUD.get_user_by_uid(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    groups = GroupCRUD.get_user_groups(user, skip, limit)
    
    # Convert to summary format
    summaries = []
    for group in groups:
        summary = GroupSummary(
            uid=group.uid,
            name=group.name,
            description=group.description,
            group_type=group.group_type,
            category=group.category,
            members_count=group.members_count,
            profile_picture_url=group.profile_picture_url
        )
        summaries.append(summary)
    
    return summaries

@router.get("/owned/{user_id}", response_model=List[GroupSummary])
async def get_owned_groups(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Get groups owned by user"""
    user = UserCRUD.get_user_by_uid(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    groups = GroupCRUD.get_owned_groups(user, skip, limit)
    
    # Convert to summary format
    summaries = []
    for group in groups:
        summary = GroupSummary(
            uid=group.uid,
            name=group.name,
            description=group.description,
            group_type=group.group_type,
            category=group.category,
            members_count=group.members_count,
            profile_picture_url=group.profile_picture_url
        )
        summaries.append(summary)
    
    return summaries
