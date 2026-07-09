from app.core.database import Base
from app.core.enums import SERVICE_DESK_CAPABILITIES, ServiceDeskAccessType
from app.modules.access.models import ServiceDeskUser, ServiceDeskUserCapability


def test_service_desk_access_tables_are_registered():
    assert ServiceDeskUser.__tablename__ in Base.metadata.tables
    assert ServiceDeskUserCapability.__tablename__ in Base.metadata.tables


def test_service_desk_access_model_keeps_roles_separate_from_projects():
    assert [item.value for item in ServiceDeskAccessType] == ["manager", "service_desk_admin"]
    assert "project_manager" not in {item.value for item in ServiceDeskAccessType}
    assert "service_desk.manage_access" in SERVICE_DESK_CAPABILITIES
