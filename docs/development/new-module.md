# Creating a module

```powershell
.\dev.cmd create-module documents
```

The generator creates bounded backend/frontend roots, health endpoints, a
manifest, lazy routes, a query-key factory, executable health test, locked-uv
Dockerfile, package manifests, and README. Workspace globs discover the new
backend and frontend automatically.

After generation:

1. Register the manifest in the shell module registry.
2. Run `uv lock` and `npm install` to record the new workspace packages.
3. Add the module API route to the gateway and Compose profile.
4. Run `.\dev.cmd architecture-check`, module tests, and contract generation.

The generator deliberately does not create business entities, database tables,
or permissions beyond the example access permission.
