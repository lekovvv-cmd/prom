from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from access_service.api.schemas import MockLoginInput, ModuleOut, RoleInput, RoleOut, SessionOut, TokenOut, UserOut, UserRolesInput
from access_service.application.access import find_user_by_email, mark_login, modules_for_permissions, permissions_for, record_audit, require_user
from access_service.domain.models import Permission, PlatformUser, Role, UserRoleAssignment
from access_service.infrastructure.database import get_session
from access_service.infrastructure.identity import InternalTokenSigner


router = APIRouter()


def serialize_user(user: PlatformUser) -> UserOut:
    return UserOut(id=user.id, external_subject=user.external_subject, email=user.email, display_name=user.display_name, department=user.department, position=user.position, is_active=user.is_active)


def serialize_session(user: PlatformUser) -> SessionOut:
    permissions = permissions_for(user)
    return SessionOut(
        user=serialize_user(user),
        modules=[ModuleOut(**item) for item in modules_for_permissions(permissions)],
        permissions=sorted(permissions),
    )


def current_user(request: Request, session: Session = Depends(get_session)) -> PlatformUser:
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    signer: InternalTokenSigner = request.app.state.token_signer
    try:
        import jwt

        claims = jwt.decode(authorization.removeprefix("Bearer "), signer.public_key, algorithms=["RS256"], audience=["projects", "service-desk"], issuer=signer.settings.token_issuer)
        return require_user(session, str(claims["sub"]))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid platform token") from exc


def platform_admin(user: PlatformUser = Depends(current_user)) -> PlatformUser:
    if "platform.admin" not in permissions_for(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform administrator permission is required")
    return user


@router.get("/.well-known/jwks.json")
def jwks(request: Request) -> dict[str, object]:
    signer: InternalTokenSigner = request.app.state.token_signer
    return signer.jwks()


@router.post("/auth/mock/login", response_model=TokenOut)
def mock_login(payload: MockLoginInput, request: Request, session: Session = Depends(get_session)) -> TokenOut:
    user = find_user_by_email(session, payload.email)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Demo user is unavailable")
    permissions = permissions_for(user)
    mark_login(session, user)
    record_audit(session, actor_user_id=user.id, action="mock_login", object_type="platform_user", object_id=user.id, request_id=getattr(request.state, "request_id", None))
    session.commit()
    signer: InternalTokenSigner = request.app.state.token_signer
    return TokenOut(access_token=signer.issue(user_id=user.id, external_subject=user.external_subject, email=user.email, permissions=permissions), session=serialize_session(user))


@router.get("/api/v1/session", response_model=SessionOut)
def session_info(user: PlatformUser = Depends(current_user)) -> SessionOut:
    return serialize_session(user)


@router.get("/api/v1/me", response_model=UserOut)
def me(user: PlatformUser = Depends(current_user)) -> UserOut:
    return serialize_user(user)


@router.get("/api/v1/me/modules", response_model=list[ModuleOut])
def my_modules(user: PlatformUser = Depends(current_user)) -> list[ModuleOut]:
    return [ModuleOut(**item) for item in modules_for_permissions(permissions_for(user))]


@router.get("/api/v1/me/permissions", response_model=list[str])
def my_permissions(user: PlatformUser = Depends(current_user)) -> list[str]:
    return sorted(permissions_for(user))


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
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unknown role code")
    before = {"role_codes": sorted(assignment.role.code for assignment in user.assignments)}
    user.assignments.clear()
    for role in roles:
        user.assignments.append(UserRoleAssignment(role=role, assigned_by_user_id=actor.id))
    record_audit(session, actor_user_id=actor.id, action="roles_replaced", object_type="platform_user", object_id=user.id, before=before, after={"role_codes": sorted(payload.role_codes)}, request_id=getattr(request.state, "request_id", None))
    session.commit()
    session.refresh(user)
    return serialize_user(require_user(session, user.id))


@router.get("/api/v1/admin/roles", response_model=list[RoleOut])
def roles(_: PlatformUser = Depends(platform_admin), session: Session = Depends(get_session)) -> list[RoleOut]:
    result = session.scalars(select(Role).options(selectinload(Role.permissions)).order_by(Role.code)).all()
    return [RoleOut(id=role.id, code=role.code, title=role.title, permissions=sorted(permission.code for permission in role.permissions)) for role in result]


def upsert_role(payload: RoleInput, request: Request, actor: PlatformUser, session: Session, role: Role | None = None) -> RoleOut:
    permissions = session.scalars(select(Permission).where(Permission.code.in_(payload.permissions))).all()
    if len(permissions) != len(set(payload.permissions)):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unknown permission code")
    if role is None:
        role = Role(code=payload.code, title=payload.title)
        session.add(role)
        action = "role_created"
    else:
        action = "role_updated"
        role.code, role.title = payload.code, payload.title
    role.permissions = permissions
    session.flush()
    record_audit(session, actor_user_id=actor.id, action=action, object_type="role", object_id=role.id, after={"code": role.code, "permissions": sorted(permission.code for permission in permissions)}, request_id=getattr(request.state, "request_id", None))
    session.commit()
    return RoleOut(id=role.id, code=role.code, title=role.title, permissions=sorted(permission.code for permission in role.permissions))


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
