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
