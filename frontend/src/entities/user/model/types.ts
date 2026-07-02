export type UserRole = "employee" | "project_manager" | "admin";

export type User = {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  department?: string | null;
  position?: string | null;
  created_at: string;
  updated_at: string;
};
