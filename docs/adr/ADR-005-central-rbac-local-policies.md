# ADR-005: Central RBAC, local policies

Permissions are centralized for module access; object-level rules remain in
the module that owns the object and workflow.

Access computes effective permissions as the union of direct roles and roles
assigned through groups. Modules are active database records, and a permission
belongs to at most one product module. Role creation rejects dangling or
cross-module permissions. Membership and role mutations increment affected
session versions, append before/after audit events, and cannot remove the final
effective platform administrator.

Product backends still enforce ownership, privacy, workflow state, optimistic
version, and row-level decisions. A central permission never bypasses a local
object policy unless that policy explicitly defines platform-admin access.
