export type UserRole = "employee" | "project_manager" | "admin";

export type User = {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  department?: string | null;
  position?: string | null;
  competencies?: string | null;
  about?: string | null;
  created_at: string;
  updated_at: string;
};

export type UserProfilePayload = {
  full_name: string;
  department?: string | null;
  position?: string | null;
  competencies?: string | null;
  about?: string | null;
};
