export type ServiceDeskNotification = {
  id: string;
  recipient_user_id: string;
  ticket_id: string | null;
  event_type: string;
  title: string;
  body: string;
  is_read: boolean;
  created_at: string;
  read_at: string | null;
};

export type ServiceDeskContextualCounters = {
  waiting_my_approval: number;
  assigned_to_me: number;
  awaiting_my_response: number;
  sla_breaches: number | null;
};
