import uuid

from app.modules.access.bootstrap import repair_service_desk_users
from app.modules.access.models import ServiceDeskUser, ServiceDeskUserCapability


def test_identity_bootstrap_repairs_old_uuid_and_replaces_demo_capabilities(db_session_factory):
    old_identity = str(uuid.uuid4())
    actual_projects_id = str(uuid.uuid4())
    with db_session_factory() as db:
        db.add(
            ServiceDeskUser(
                identity_user_id=old_identity,
                email="sd.manager@utmn.ru",
                display_name="Старое имя",
                department="Old",
                position="Old",
            )
        )
        db.flush()
        user = db.query(ServiceDeskUser).filter_by(email="sd.manager@utmn.ru").one()
        db.add(
            ServiceDeskUserCapability(
                service_desk_user_id=user.id,
                capability="service_desk.manage_catalog",
            )
        )
        db.commit()

        result = repair_service_desk_users(
            db,
            [
                {
                    "id": actual_projects_id,
                    "email": "sd.manager@utmn.ru",
                    "full_name": "Менеджер SD",
                    "department": "Service Desk",
                    "position": "Менеджер",
                },
                {"id": str(uuid.uuid4()), "email": "unknown@example.com"},
            ],
        )
        db.commit()

        user = db.query(ServiceDeskUser).filter_by(email="sd.manager@utmn.ru").one()
        assert result.updated == 1
        assert result.skipped == 1
        assert user.identity_user_id == actual_projects_id
        assert user.display_name == "Менеджер SD"
        assert user.department == "Service Desk"
        assert {item.capability for item in user.capabilities} == {
            "service_desk.be_assignee",
            "service_desk.approve",
            "service_desk.assign",
            "service_desk.change_priority",
            "service_desk.view_all_tickets",
        }
        assert db.query(ServiceDeskUserCapability).filter_by(service_desk_user_id=user.id).count() > 0

        second = repair_service_desk_users(
            db,
            [
                {
                    "id": actual_projects_id,
                    "email": "sd.manager@utmn.ru",
                    "full_name": "Менеджер SD",
                }
            ],
        )
        db.commit()
        assert second.created == 0
        assert db.query(ServiceDeskUser).filter_by(email="sd.manager@utmn.ru").count() == 1


def test_identity_bootstrap_revokes_demo_users_without_service_desk_role(
    db_session_factory,
):
    identities = {
        email: str(uuid.uuid4())
        for email in (
            "employee@utmn.ru",
            "project.manager@utmn.ru",
            "admin@utmn.ru",
        )
    }
    with db_session_factory() as db:
        for email, identity_user_id in identities.items():
            db.add(
                ServiceDeskUser(
                    identity_user_id=identity_user_id,
                    email=email,
                    display_name=email,
                    is_active=True,
                )
            )
        db.commit()

        repair_service_desk_users(
            db,
            [
                {"id": identity_user_id, "email": email, "full_name": email}
                for email, identity_user_id in identities.items()
            ],
        )
        db.commit()

        assert all(
            not user.is_active
            for user in db.query(ServiceDeskUser).filter(
                ServiceDeskUser.email.in_(identities)
            )
        )
