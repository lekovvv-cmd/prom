import { Header } from "../../header/ui/Header";
import { ServiceDeskAdminNav } from "../../service-desk-admin-nav/ui/ServiceDeskAdminNav";

export function ServiceDeskAdminLayout({ children, showHeader = true }: { children: React.ReactNode; showHeader?: boolean }) {
  return <>{showHeader ? <Header /> : null}<ServiceDeskAdminNav />{children}</>;
}
