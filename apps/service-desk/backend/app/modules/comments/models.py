from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utc_now
from app.core.enums import ServiceDeskCommentVisibility, enum_values
from app.modules.access.models import ServiceDeskUser

if TYPE_CHECKING:
    from app.modules.tickets.models import ServiceDeskTicket


class ServiceDeskTicketComment(Base):
    __tablename__ = "service_desk_comments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_tickets.id"),
        index=True,
        nullable=False,
    )
    author_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_desk_users.id"),
        nullable=False,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[ServiceDeskCommentVisibility] = mapped_column(
        SAEnum(
            ServiceDeskCommentVisibility,
            values_callable=enum_values,
            native_enum=False,
            length=16,
        ),
        nullable=False,
        default=ServiceDeskCommentVisibility.PUBLIC,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    ticket: Mapped["ServiceDeskTicket"] = relationship(back_populates="comments")
    author: Mapped[ServiceDeskUser] = relationship()
