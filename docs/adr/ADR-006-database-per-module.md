# ADR-006: Database per module

Every product service owns an isolated database and credentials. Cross-module
SQL reads are forbidden.

