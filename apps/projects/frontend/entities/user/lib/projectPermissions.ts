export function canManageProjects(
  hasPermission: (permission: string) => boolean,
) {
  return hasPermission("projects.create") || hasPermission("projects.manage");
}
