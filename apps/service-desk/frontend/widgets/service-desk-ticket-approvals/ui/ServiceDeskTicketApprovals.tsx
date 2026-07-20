import { Check, Clock3, Minus, X } from "lucide-react";

import {
  findCurrentUserApproval,
  getTicketActionAvailability,
} from "../../../entities/service-desk-ticket/lib/ticketActions";
import type {
  ServiceDeskApprovalStatus,
  ServiceDeskTicket,
} from "../../../entities/service-desk-ticket/model/types";
import { ApproveTicketButton } from "../../../features/approve-ticket/ui/ApproveTicketButton";
import { RejectTicketButton } from "../../../features/reject-ticket/ui/RejectTicketButton";
import { formatDateTime } from "@prom/utils/date";
import { Badge, type BadgeTone } from "@prom/ui/Badge";
import { Card } from "@prom/ui/Card";

const approvalStatusMeta: Record<
  ServiceDeskApprovalStatus,
  { label: string; tone: BadgeTone; icon: typeof Clock3 }
> = {
  pending: { label: "Ожидает решения", tone: "warning", icon: Clock3 },
  approved: { label: "Согласовано", tone: "success", icon: Check },
  rejected: { label: "Отклонено", tone: "danger", icon: X },
  skipped: { label: "Пропущено", tone: "muted", icon: Minus },
};

export function ServiceDeskTicketApprovals({
  currentUserId,
  ticket,
  onTicketChanged,
}: {
  currentUserId: string;
  ticket: ServiceDeskTicket;
  onTicketChanged: (ticket: ServiceDeskTicket) => void;
}) {
  const currentApproval = findCurrentUserApproval(ticket, currentUserId);
  const { canApprove, canReject } = getTicketActionAvailability(
    ticket.allowed_actions,
  );

  return (
    <Card className="service-desk-approvals">
      <div className="service-desk-section-heading">
        <div>
          <span className="service-desk-eyebrow">Маршрут решения</span>
          <h3>Согласование</h3>
        </div>
        <Badge
          tone={ticket.status === "pending_approval" ? "warning" : "neutral"}
        >
          {ticket.approval_stages.length} этапа(ов)
        </Badge>
      </div>

      {ticket.approval_stages.length === 0 ? (
        <p className="muted">Для этой заявки согласование не требовалось.</p>
      ) : (
        <ol className="approval-stage-list">
          {ticket.approval_stages.map((stage) => {
            const isCurrent =
              stage.status === "pending" && Boolean(stage.started_at);
            const stageMeta = approvalStatusMeta[stage.status];
            return (
              <li
                className={`approval-stage ${isCurrent ? "approval-stage-current" : ""}`}
                key={stage.id}
              >
                <div className="approval-stage-marker">
                  {stage.position + 1}
                </div>
                <div className="approval-stage-content">
                  <div className="approval-stage-header">
                    <div>
                      <h4>{stage.title}</h4>
                      <span>
                        Правило:{" "}
                        {stage.decision_rule === "any"
                          ? "достаточно одного"
                          : "нужны все"}
                      </span>
                    </div>
                    <Badge tone={stageMeta.tone}>{stageMeta.label}</Badge>
                  </div>
                  <ul className="approval-person-list">
                    {stage.approvals.map((approval) => {
                      const meta = approvalStatusMeta[approval.status];
                      const StatusIcon = meta.icon;
                      return (
                        <li key={approval.id}>
                          <span
                            className={`approval-person-icon badge-${meta.tone}`}
                          >
                            <StatusIcon size={14} />
                          </span>
                          <div>
                            <strong>{approval.approver_display_name}</strong>
                            <span>
                              {meta.label}
                              {approval.decided_at
                                ? ` · ${formatDateTime(approval.decided_at)}`
                                : ""}
                            </span>
                            {approval.decision_comment && (
                              <p>{approval.decision_comment}</p>
                            )}
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              </li>
            );
          })}
        </ol>
      )}

      {currentApproval && (canApprove || canReject) && (
        <div className="approval-action-panel">
          <div>
            <strong>Требуется ваше решение</strong>
          </div>
          <div className="button-row">
            {canApprove && (
              <ApproveTicketButton
                ticketId={ticket.id}
                approvalId={currentApproval.id}
                onCompleted={onTicketChanged}
              />
            )}
            {canReject && (
              <RejectTicketButton
                ticketId={ticket.id}
                approvalId={currentApproval.id}
                onCompleted={onTicketChanged}
              />
            )}
          </div>
        </div>
      )}
    </Card>
  );
}
