# Backups and recovery

Back up each module database independently and verify restore into an isolated
environment. Restore schema-compatible snapshots before application startup;
run migrations with the documented expand/contract sequence. Files are backed
up with their module storage prefix and restored only after metadata integrity
has been checked. Never reset production volumes to recover an application.

