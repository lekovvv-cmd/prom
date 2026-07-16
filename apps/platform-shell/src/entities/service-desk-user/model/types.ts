export type ServiceDeskUser = {
  id: string;
  identity_user_id: string;
  email: string;
  display_name: string;
  department: string | null;
  position: string | null;
  access_type: "service_desk_manager" | "service_desk_admin";
  is_active: boolean;
  capabilities: string[];
  created_at: string;
  updated_at: string;
};
