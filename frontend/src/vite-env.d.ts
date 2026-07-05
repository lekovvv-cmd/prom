/// <reference types="vite/client" />

declare module "lucide-react" {
  import type { FC, SVGProps } from "react";

  type Icon = FC<SVGProps<SVGSVGElement> & { size?: number | string }>;

  export const Archive: Icon;
  export const ArchiveRestore: Icon;
  export const BarChart3: Icon;
  export const CalendarCheck: Icon;
  export const CheckCircle2: Icon;
  export const Edit3: Icon;
  export const FileCheck2: Icon;
  export const FileText: Icon;
  export const FolderKanban: Icon;
  export const LogIn: Icon;
  export const LogOut: Icon;
  export const Lock: Icon;
  export const MessageSquare: Icon;
  export const Paperclip: Icon;
  export const Plus: Icon;
  export const Send: Icon;
  export const Table2: Icon;
  export const Trash2: Icon;
  export const UserRound: Icon;
  export const X: Icon;
}
