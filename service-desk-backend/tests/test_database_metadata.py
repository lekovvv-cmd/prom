from app.core.database import Base
from app.core.enums import SERVICE_DESK_CAPABILITIES, ServiceDeskAccessType
from app.modules.access.models import ServiceDeskUser, ServiceDeskUserCapability
from app.modules.approvals.models import (
    ServiceDeskApprovalStage,
    ServiceDeskApprovalStageApprover,
    ServiceDeskApprovalWorkflow,
    ServiceDeskTicketApproval,
    ServiceDeskTicketApprovalStage,
)
from app.modules.catalog.models import ServiceDeskCategory, ServiceDeskService
from app.modules.sla.models import (
    ServiceDeskBusinessCalendar,
    ServiceDeskBusinessHours,
    ServiceDeskCalendarException,
)
from app.modules.templates.models import (
    ServiceDeskDictionary,
    ServiceDeskDictionaryItem,
    ServiceDeskTemplateField,
    ServiceDeskTemplateVersion,
)
from app.modules.tickets.models import (
    ServiceDeskTicket,
    ServiceDeskTicketCounter,
    ServiceDeskTicketHistory,
)


def test_service_desk_access_tables_are_registered():
    assert ServiceDeskUser.__tablename__ in Base.metadata.tables
    assert ServiceDeskUserCapability.__tablename__ in Base.metadata.tables
    assert ServiceDeskApprovalWorkflow.__tablename__ in Base.metadata.tables
    assert ServiceDeskApprovalStage.__tablename__ in Base.metadata.tables
    assert ServiceDeskApprovalStageApprover.__tablename__ in Base.metadata.tables
    assert ServiceDeskTicketApprovalStage.__tablename__ in Base.metadata.tables
    assert ServiceDeskTicketApproval.__tablename__ in Base.metadata.tables
    assert ServiceDeskCategory.__tablename__ in Base.metadata.tables
    assert ServiceDeskService.__tablename__ in Base.metadata.tables
    assert ServiceDeskTemplateVersion.__tablename__ in Base.metadata.tables
    assert ServiceDeskTemplateField.__tablename__ in Base.metadata.tables
    assert ServiceDeskDictionary.__tablename__ in Base.metadata.tables
    assert ServiceDeskDictionaryItem.__tablename__ in Base.metadata.tables
    assert ServiceDeskTicket.__tablename__ in Base.metadata.tables
    assert ServiceDeskTicketCounter.__tablename__ in Base.metadata.tables
    assert ServiceDeskTicketHistory.__tablename__ in Base.metadata.tables
    assert ServiceDeskBusinessCalendar.__tablename__ in Base.metadata.tables
    assert ServiceDeskBusinessHours.__tablename__ in Base.metadata.tables
    assert ServiceDeskCalendarException.__tablename__ in Base.metadata.tables


def test_service_desk_access_model_keeps_roles_separate_from_projects():
    assert [item.value for item in ServiceDeskAccessType] == [
        "service_desk_manager",
        "service_desk_admin",
    ]
    assert "project_manager" not in {item.value for item in ServiceDeskAccessType}
    assert "service_desk.manage_access" in SERVICE_DESK_CAPABILITIES
