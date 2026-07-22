from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from access_service.api.schemas import (
    GroupInput,
    GroupOut,
    MockCodeInput,
    MockCodeOut,
    MockLoginInput,
    ModuleAdminOut,
    ModuleInput,
    ModuleOut,
    RoleInput,
    RoleOut,
    SessionOut,
    TokenOut,
    UserOut,
    UserRolesInput,
)
from access_service.application.access import (
    affected_users_for_role,
    find_user_by_email,
    mark_login,
    modules_for_permissions,
    permissions_for,
    record_audit,
    require_user,
    revoke_sessions,
    sync_external_principal,
    user_ids_for_permission,
)
from access_service.domain.models import (
    Group,
    GroupMembership,
    GroupRoleAssignment,
    Module,
    Permission,
    PlatformUser,
    Role,
    UserRoleAssignment,
)
from access_service.infrastructure.database import get_session
from access_service.infrastructure.identity import IdentityProvider, InternalTokenSigner
from access_service.infrastructure.sessions import BrowserSessionManager


router = APIRouter()


def safe_return_url(return_url: str) -> str:
    if return_url.startswith("/") and not return_url.startswith("//"):
        return return_url
    return "/"


def serialize_user(user: PlatformUser) -> UserOut:
    return UserOut(
        id=user.id,
        external_subject=user.external_subject,
        email=user.email,
        display_name=user.display_name,
        department=user.department,
        position=user.position,
        is_active=user.is_active,
        session_version=user.session_version,
    )


def serialize_session(session: Session, user: PlatformUser) -> SessionOut:
    permissions = permissions_for(session, user)
    return SessionOut(
        user=serialize_user(user),
        modules=[
            ModuleOut.model_validate(item)
            for item in modules_for_permissions(session, permissions)
        ],
        permissions=sorted(permissions),
    )


def current_user(
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
) -> PlatformUser:
    session_manager: BrowserSessionManager = request.app.state.session_manager
    if request.cookies.get(session_manager.settings.session_cookie_name):
        return session_manager.authenticate(request, response, session)
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    signer: InternalTokenSigner = request.app.state.token_signer
    try:
        claims = signer.verify(
            authorization.removeprefix("Bearer "),
            audience=list(signer.settings.token_audience_values),
        )
        user = require_user(session, str(claims["sub"]))
        if claims.get("sv") != user.session_version:
            raise ValueError("The platform session was revoked")
        return user
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid platform token") from exc


def platform_admin(
    user: PlatformUser = Depends(current_user),
    session: Session = Depends(get_session),
) -> PlatformUser:
    if "platform.admin" not in permissions_for(session, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform administrator permission is required")
    return user


@router.get("/.well-known/jwks.json")
def jwks(request: Request) -> dict[str, list[dict[str, str]]]:
    signer: InternalTokenSigner = request.app.state.token_signer
    return signer.jwks()


def issue_token(request: Request, session: Session, user: PlatformUser) -> TokenOut:
    signer: InternalTokenSigner = request.app.state.token_signer
    return TokenOut(
        access_token=signer.issue(
            user_id=user.id,
            external_subject=user.external_subject,
            email=user.email,
            display_name=user.display_name,
            permissions=permissions_for(session, user),
            session_version=user.session_version,
            correlation_id=getattr(request.state, "request_id", None),
        ),
        session=serialize_session(session, user),
    )


def require_mock_provider(request: Request) -> None:
    signer: InternalTokenSigner = request.app.state.token_signer
    if signer.settings.environment.lower() in {"production", "prod"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if signer.settings.sso_provider != "mock":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


@router.post("/auth/mock/code", response_model=MockCodeOut)
def mock_code(payload: MockCodeInput, request: Request) -> MockCodeOut:
    require_mock_provider(request)
    return MockCodeOut(email=payload.email.lower(), dev_code="000000")


def require_mock_user(
    payload: MockLoginInput,
    request: Request,
    session: Session,
) -> PlatformUser:
    require_mock_provider(request)
    if payload.code != "000000":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid mock code")
    user = find_user_by_email(session, payload.email)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Demo user is unavailable")
    return user


def start_browser_session(
    *,
    request: Request,
    response: Response,
    session: Session,
    user: PlatformUser,
    action: str,
) -> SessionOut:
    mark_login(session, user)
    manager: BrowserSessionManager = request.app.state.session_manager
    credentials = manager.create(session, user)
    record_audit(
        session,
        actor_user_id=user.id,
        action=action,
        object_type="browser_session",
        object_id=user.id,
        request_id=getattr(request.state, "request_id", None),
    )
    session.commit()
    manager.set_cookies(response, credentials)
    return serialize_session(session, user)


@router.post("/auth/mock/verify", response_model=SessionOut)
def mock_verify(
    payload: MockLoginInput,
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
) -> SessionOut:
    user = require_mock_user(payload, request, session)
    return start_browser_session(
        request=request,
        response=response,
        session=session,
        user=user,
        action="mock_session_created",
    )


@router.post("/auth/mock/token", response_model=TokenOut)
def mock_token(payload: MockLoginInput, request: Request, session: Session = Depends(get_session)) -> TokenOut:
    user = require_mock_user(payload, request, session)
    mark_login(session, user)
    record_audit(session, actor_user_id=user.id, action="mock_login", object_type="platform_user", object_id=user.id, request_id=getattr(request.state, "request_id", None))
    session.commit()
    return issue_token(request, session, user)


@router.post("/auth/mock/logout", status_code=status.HTTP_204_NO_CONTENT)
def mock_logout(
    request: Request,
    response: Response,
    user: PlatformUser = Depends(current_user),
    session: Session = Depends(get_session),
) -> None:
    manager: BrowserSessionManager = request.app.state.session_manager
    manager.revoke_current(request, session)
    record_audit(
        session,
        actor_user_id=user.id,
        action="mock_logout",
        object_type="platform_user",
        object_id=user.id,
        request_id=getattr(request.state, "request_id", None),
    )
    session.commit()
    manager.clear_cookies(response)


@router.get("/auth/login", response_model=None)
def login(
    request: Request,
    return_url: str = "/",
    session: Session = Depends(get_session),
) -> RedirectResponse:
    provider: IdentityProvider = request.app.state.identity_provider
    principal = provider.authenticate_request(request)
    if principal is None:
        return RedirectResponse(provider.build_login_redirect(return_url), status_code=302)
    user = sync_external_principal(session, principal)
    target = safe_return_url(principal.return_url or return_url)
    response = RedirectResponse(target, status_code=302)
    start_browser_session(
        request=request,
        response=response,
        session=session,
        user=user,
        action="sso_session_created",
    )
    return response


@router.get("/auth/callback", response_model=None)
def oidc_callback(
    request: Request,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    provider: IdentityProvider = request.app.state.identity_provider
    principal = provider.handle_callback(request)
    user = sync_external_principal(session, principal)
    response = RedirectResponse(safe_return_url(principal.return_url or "/"), status_code=302)
    start_browser_session(
        request=request,
        response=response,
        session=session,
        user=user,
        action="oidc_session_created",
    )
    return response


@router.post("/auth/logout", response_model=None)
def logout(
    request: Request,
    return_url: str = "/",
    user: PlatformUser = Depends(current_user),
    session: Session = Depends(get_session),
) -> RedirectResponse:
    manager: BrowserSessionManager = request.app.state.session_manager
    manager.revoke_current(request, session)
    record_audit(
        session,
        actor_user_id=user.id,
        action="sso_logout",
        object_type="platform_user",
        object_id=user.id,
        request_id=getattr(request.state, "request_id", None),
    )
    session.commit()
    provider: IdentityProvider = request.app.state.identity_provider
    response = RedirectResponse(
        provider.build_logout_redirect(safe_return_url(return_url)),
        status_code=302,
    )
    manager.clear_cookies(response)
    return response


@router.get("/api/v1/session", response_model=SessionOut)
def session_info(
    user: PlatformUser = Depends(current_user),
    session: Session = Depends(get_session),
) -> SessionOut:
    return serialize_session(session, user)


@router.get("/api/v1/session/token", response_model=TokenOut)
def session_token(
    request: Request,
    user: PlatformUser = Depends(current_user),
    session: Session = Depends(get_session),
) -> TokenOut:
    """Issue a short-lived, memory-only bearer for product API calls."""

    return issue_token(request, session, user)


@router.delete("/api/v1/session", status_code=status.HTTP_204_NO_CONTENT)
def close_session(
    request: Request,
    response: Response,
    user: PlatformUser = Depends(current_user),
    session: Session = Depends(get_session),
) -> None:
    manager: BrowserSessionManager = request.app.state.session_manager
    manager.revoke_current(request, session)
    record_audit(
        session,
        actor_user_id=user.id,
        action="browser_session_revoked",
        object_type="browser_session",
        object_id=user.id,
        request_id=getattr(request.state, "request_id", None),
    )
    session.commit()
    manager.clear_cookies(response)


@router.get("/api/v1/me", response_model=UserOut)
def me(user: PlatformUser = Depends(current_user)) -> UserOut:
    return serialize_user(user)


@router.get("/api/v1/me/modules", response_model=list[ModuleOut])
def my_modules(
    user: PlatformUser = Depends(current_user),
    session: Session = Depends(get_session),
) -> list[ModuleOut]:
    return [
        ModuleOut.model_validate(item)
        for item in modules_for_permissions(session, permissions_for(session, user))
    ]


@router.get("/api/v1/me/permissions", response_model=list[str])
def my_permissions(
    user: PlatformUser = Depends(current_user),
    session: Session = Depends(get_session),
) -> list[str]:
    return sorted(permissions_for(session, user))


@router.get("/api/v1/admin/users", response_model=list[UserOut])
def users(_: PlatformUser = Depends(platform_admin), session: Session = Depends(get_session)) -> list[UserOut]:
    return [serialize_user(user) for user in session.scalars(select(PlatformUser).order_by(PlatformUser.email)).all()]


@router.get("/api/v1/admin/users/{user_id}", response_model=UserOut)
def user_detail(user_id: str, _: PlatformUser = Depends(platform_admin), session: Session = Depends(get_session)) -> UserOut:
    try:
        return serialize_user(require_user(session, user_id))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User was not found") from exc


@router.put("/api/v1/admin/users/{user_id}/roles", response_model=UserOut)
def replace_user_roles(user_id: str, payload: UserRolesInput, request: Request, actor: PlatformUser = Depends(platform_admin), session: Session = Depends(get_session)) -> UserOut:
    try:
        user = require_user(session, user_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User was not found") from exc
    roles = session.scalars(select(Role).where(Role.code.in_(payload.role_codes))).all()
    if len(roles) != len(set(payload.role_codes)):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown role code")
    before: dict[str, object] = {
        "role_codes": sorted(assignment.role.code for assignment in user.assignments)
    }
    user.assignments.clear()
    for role in roles:
        user.assignments.append(UserRoleAssignment(role=role, assigned_by_user_id=actor.id))
    session.flush()
    ensure_platform_admin_exists(session)
    revoke_sessions(session, user)
    record_audit(session, actor_user_id=actor.id, action="roles_replaced", object_type="platform_user", object_id=user.id, before=before, after={"role_codes": sorted(payload.role_codes)}, request_id=getattr(request.state, "request_id", None))
    session.commit()
    session.refresh(user)
    return serialize_user(require_user(session, user.id))


@router.get("/api/v1/admin/roles", response_model=list[RoleOut])
def roles(_: PlatformUser = Depends(platform_admin), session: Session = Depends(get_session)) -> list[RoleOut]:
    result = session.scalars(select(Role).options(selectinload(Role.permissions)).order_by(Role.code)).all()
    return [serialize_role(role) for role in result]


def serialize_role(role: Role) -> RoleOut:
    return RoleOut(
        id=role.id,
        code=role.code,
        title=role.title,
        module_id=role.module_id,
        permissions=sorted(permission.code for permission in role.permissions),
    )


def ensure_platform_admin_exists(session: Session) -> None:
    if not user_ids_for_permission(session, "platform.admin"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The last platform administrator cannot be removed",
        )


def validate_role_integrity(
    *,
    session: Session,
    payload: RoleInput,
    permissions: list[Permission],
    role: Role | None,
) -> None:
    if payload.module_id is not None:
        module = session.get(Module, payload.module_id)
        if module is None or not module.is_active:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Role module is unknown or inactive",
            )
        wrong_module = [
            permission.code
            for permission in permissions
            if permission.module_id != payload.module_id
        ]
        if wrong_module:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "code": "role_permission_module_mismatch",
                    "permissions": sorted(wrong_module),
                },
            )
        return
    is_platform_admin_role = (
        (role is not None and role.is_system and role.code == "platform_admin")
        or payload.code == "platform_admin"
    )
    dangling_product_permissions = [
        permission.code
        for permission in permissions
        if permission.module_id is not None
    ]
    if dangling_product_permissions and not is_platform_admin_role:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "platform_role_cannot_hold_module_permission",
                "permissions": sorted(dangling_product_permissions),
            },
        )


def upsert_role(payload: RoleInput, request: Request, actor: PlatformUser, session: Session, role: Role | None = None) -> RoleOut:
    permissions = session.scalars(select(Permission).where(Permission.code.in_(payload.permissions))).all()
    if len(permissions) != len(set(payload.permissions)):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown permission code")
    validate_role_integrity(
        session=session,
        payload=payload,
        permissions=list(permissions),
        role=role,
    )
    affected_users: list[PlatformUser] = []
    before: dict[str, object] | None = None
    if role is None:
        role = Role(code=payload.code, title=payload.title, module_id=payload.module_id)
        session.add(role)
        action = "role_created"
    else:
        action = "role_updated"
        affected_users = affected_users_for_role(session, role.id)
        before = {
            "code": role.code,
            "title": role.title,
            "module_id": role.module_id,
            "permissions": sorted(permission.code for permission in role.permissions),
        }
        role.code, role.title, role.module_id = payload.code, payload.title, payload.module_id
    role.permissions = list(permissions)
    session.flush()
    ensure_platform_admin_exists(session)
    record_audit(session, actor_user_id=actor.id, action=action, object_type="role", object_id=role.id, before=before, after={"code": role.code, "title": role.title, "module_id": role.module_id, "permissions": sorted(permission.code for permission in permissions)}, request_id=getattr(request.state, "request_id", None))
    for user in affected_users:
        revoke_sessions(session, user)
    session.commit()
    return serialize_role(role)


@router.post("/api/v1/admin/roles", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(payload: RoleInput, request: Request, actor: PlatformUser = Depends(platform_admin), session: Session = Depends(get_session)) -> RoleOut:
    if session.scalar(select(Role.id).where(Role.code == payload.code)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role code already exists")
    return upsert_role(payload, request, actor, session)


@router.patch("/api/v1/admin/roles/{role_id}", response_model=RoleOut)
def patch_role(role_id: str, payload: RoleInput, request: Request, actor: PlatformUser = Depends(platform_admin), session: Session = Depends(get_session)) -> RoleOut:
    role = session.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role was not found")
    return upsert_role(payload, request, actor, session, role)


@router.get("/api/v1/admin/modules", response_model=list[ModuleAdminOut])
def admin_modules(
    _: PlatformUser = Depends(platform_admin),
    session: Session = Depends(get_session),
) -> list[ModuleAdminOut]:
    modules = session.scalars(select(Module).order_by(Module.id)).all()
    return [
        ModuleAdminOut(id=module.id, title=module.title, is_active=module.is_active)
        for module in modules
    ]


@router.post(
    "/api/v1/admin/modules",
    response_model=ModuleAdminOut,
    status_code=status.HTTP_201_CREATED,
)
def register_module(
    payload: ModuleInput,
    request: Request,
    actor: PlatformUser = Depends(platform_admin),
    session: Session = Depends(get_session),
) -> ModuleAdminOut:
    if session.get(Module, payload.id) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Module already exists")
    module = Module(id=payload.id, title=payload.title, is_active=True)
    session.add(module)
    access_permission_code = f"{payload.id.replace('-', '_')}.access"
    if session.scalar(select(Permission.id).where(Permission.code == access_permission_code)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Module access permission already exists",
        )
    session.add(
        Permission(
            code=access_permission_code,
            title=f"Access {payload.title}",
            module_id=payload.id,
        )
    )
    session.flush()
    record_audit(
        session,
        actor_user_id=actor.id,
        action="module_registered",
        object_type="module",
        object_id=module.id,
        after={"id": module.id, "title": module.title, "is_active": True},
        request_id=getattr(request.state, "request_id", None),
    )
    session.commit()
    return ModuleAdminOut(id=module.id, title=module.title, is_active=module.is_active)


def serialize_group(session: Session, group: Group) -> GroupOut:
    member_ids = session.scalars(
        select(GroupMembership.user_id)
        .where(GroupMembership.group_id == group.id)
        .order_by(GroupMembership.user_id)
    ).all()
    role_codes = session.scalars(
        select(Role.code)
        .join(GroupRoleAssignment, GroupRoleAssignment.role_id == Role.id)
        .where(GroupRoleAssignment.group_id == group.id)
        .order_by(Role.code)
    ).all()
    return GroupOut(
        id=group.id,
        code=group.code,
        title=group.title,
        member_ids=list(member_ids),
        role_codes=list(role_codes),
    )


def require_group(session: Session, group_id: str) -> Group:
    group = session.get(Group, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group was not found")
    return group


def group_members(session: Session, group_id: str) -> list[PlatformUser]:
    return list(
        session.scalars(
            select(PlatformUser)
            .join(GroupMembership, GroupMembership.user_id == PlatformUser.id)
            .where(GroupMembership.group_id == group_id)
        ).all()
    )


@router.get("/api/v1/admin/groups", response_model=list[GroupOut])
def groups(
    _: PlatformUser = Depends(platform_admin),
    session: Session = Depends(get_session),
) -> list[GroupOut]:
    return [
        serialize_group(session, group)
        for group in session.scalars(select(Group).order_by(Group.code)).all()
    ]


@router.post(
    "/api/v1/admin/groups",
    response_model=GroupOut,
    status_code=status.HTTP_201_CREATED,
)
def create_group(
    payload: GroupInput,
    request: Request,
    actor: PlatformUser = Depends(platform_admin),
    session: Session = Depends(get_session),
) -> GroupOut:
    if session.scalar(select(Group.id).where(Group.code == payload.code)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Group code exists")
    group = Group(code=payload.code, title=payload.title)
    session.add(group)
    session.flush()
    record_audit(
        session,
        actor_user_id=actor.id,
        action="group_created",
        object_type="group",
        object_id=group.id,
        after={"code": group.code, "title": group.title},
        request_id=getattr(request.state, "request_id", None),
    )
    session.commit()
    return serialize_group(session, group)


@router.delete("/api/v1/admin/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: str,
    request: Request,
    actor: PlatformUser = Depends(platform_admin),
    session: Session = Depends(get_session),
) -> None:
    group = require_group(session, group_id)
    members = group_members(session, group.id)
    before = serialize_group(session, group).model_dump()
    session.delete(group)
    session.flush()
    ensure_platform_admin_exists(session)
    for user in members:
        revoke_sessions(session, user)
    record_audit(
        session,
        actor_user_id=actor.id,
        action="group_deleted",
        object_type="group",
        object_id=group_id,
        before=before,
        request_id=getattr(request.state, "request_id", None),
    )
    session.commit()


@router.put(
    "/api/v1/admin/groups/{group_id}/members/{user_id}",
    response_model=GroupOut,
)
def add_group_member(
    group_id: str,
    user_id: str,
    request: Request,
    actor: PlatformUser = Depends(platform_admin),
    session: Session = Depends(get_session),
) -> GroupOut:
    group = require_group(session, group_id)
    try:
        user = require_user(session, user_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User was not found") from exc
    exists = session.scalar(
        select(GroupMembership.id).where(
            GroupMembership.group_id == group.id,
            GroupMembership.user_id == user.id,
        )
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Membership exists")
    session.add(GroupMembership(group_id=group.id, user_id=user.id))
    session.flush()
    revoke_sessions(session, user)
    record_audit(
        session,
        actor_user_id=actor.id,
        action="group_member_added",
        object_type="group",
        object_id=group.id,
        after={"user_id": user.id},
        request_id=getattr(request.state, "request_id", None),
    )
    session.commit()
    return serialize_group(session, group)


@router.delete(
    "/api/v1/admin/groups/{group_id}/members/{user_id}",
    response_model=GroupOut,
)
def remove_group_member(
    group_id: str,
    user_id: str,
    request: Request,
    actor: PlatformUser = Depends(platform_admin),
    session: Session = Depends(get_session),
) -> GroupOut:
    group = require_group(session, group_id)
    membership = session.scalar(
        select(GroupMembership).where(
            GroupMembership.group_id == group.id,
            GroupMembership.user_id == user_id,
        )
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    user = session.get(PlatformUser, user_id)
    session.delete(membership)
    session.flush()
    ensure_platform_admin_exists(session)
    if user is not None:
        revoke_sessions(session, user)
    record_audit(
        session,
        actor_user_id=actor.id,
        action="group_member_removed",
        object_type="group",
        object_id=group.id,
        before={"user_id": user_id},
        request_id=getattr(request.state, "request_id", None),
    )
    session.commit()
    return serialize_group(session, group)


@router.put(
    "/api/v1/admin/groups/{group_id}/roles/{role_id}",
    response_model=GroupOut,
)
def add_group_role(
    group_id: str,
    role_id: str,
    request: Request,
    actor: PlatformUser = Depends(platform_admin),
    session: Session = Depends(get_session),
) -> GroupOut:
    group = require_group(session, group_id)
    role = session.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role was not found")
    exists = session.scalar(
        select(GroupRoleAssignment.id).where(
            GroupRoleAssignment.group_id == group.id,
            GroupRoleAssignment.role_id == role.id,
        )
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Group role exists")
    members = group_members(session, group.id)
    session.add(GroupRoleAssignment(group_id=group.id, role_id=role.id))
    session.flush()
    for user in members:
        revoke_sessions(session, user)
    record_audit(
        session,
        actor_user_id=actor.id,
        action="group_role_added",
        object_type="group",
        object_id=group.id,
        after={"role_code": role.code},
        request_id=getattr(request.state, "request_id", None),
    )
    session.commit()
    return serialize_group(session, group)


@router.delete(
    "/api/v1/admin/groups/{group_id}/roles/{role_id}",
    response_model=GroupOut,
)
def remove_group_role(
    group_id: str,
    role_id: str,
    request: Request,
    actor: PlatformUser = Depends(platform_admin),
    session: Session = Depends(get_session),
) -> GroupOut:
    group = require_group(session, group_id)
    assignment = session.scalar(
        select(GroupRoleAssignment).where(
            GroupRoleAssignment.group_id == group.id,
            GroupRoleAssignment.role_id == role_id,
        )
    )
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group role not found")
    role = session.get(Role, role_id)
    members = group_members(session, group.id)
    session.delete(assignment)
    session.flush()
    ensure_platform_admin_exists(session)
    for user in members:
        revoke_sessions(session, user)
    record_audit(
        session,
        actor_user_id=actor.id,
        action="group_role_removed",
        object_type="group",
        object_id=group.id,
        before={"role_code": role.code if role else role_id},
        request_id=getattr(request.state, "request_id", None),
    )
    session.commit()
    return serialize_group(session, group)
