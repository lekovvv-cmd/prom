import uuid

from app.modules.access.bootstrap import repair_service_desk_users
from app.modules.access.models import ServiceDeskUser, ServiceDeskUserCapability


def test_identity_bootstrap_repairs_old_uuid_and_preserves_demo_capabilities(db_session_factory):
    old_identity = str(uuid.uuid4())
    actual_projects_id = str(uuid.uuid4())
    with db_session_factory() as db:
        db.add(
            ServiceDeskUser(
                identity_user_id=old_identity,
                email="manager@utmn.ru",
                display_name="Старое имя",
                department="Old",
                position="Old",
            )
        )
        db.commit()

        result = repair_service_desk_users(
            db,
            [
                {
                    "id": actual_projects_id,
                    "email": "manager@utmn.ru",
                    "full_name": "Руководитель",
                    "department": "ШПИУ",
                    "position": "Руководитель проектов",
                },
                {"id": str(uuid.uuid4()), "email": "unknown@example.com"},
            ],
        )
        db.commit()

        user = db.query(ServiceDeskUser).filter_by(email="manager@utmn.ru").one()
        assert result.updated == 1
        assert result.skipped == 1
        assert user.identity_user_id == actual_projects_id
        assert user.display_name == "Руководитель"
        assert user.department == "ШПИУ"
        assert {item.capability for item in user.capabilities} >= {
            "service_desk.access",
            "service_desk.create_request",
        }
        assert db.query(ServiceDeskUserCapability).filter_by(service_desk_user_id=user.id).count() > 0
