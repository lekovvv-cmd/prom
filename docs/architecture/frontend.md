# Frontend architecture

`apps/platform-shell` owns global providers, platform routes, error/loading
states, and the module registry. Product manifests live in their product
directories and are loaded with `React.lazy`; the shell never eagerly imports
module pages. Generic transport has no product side effects. Query state belongs
to module-scoped query-key factories.

Tailwind 4.3.3 is integrated through the official Vite plugin. New shared UI
uses semantic token utilities and CVA/Radix primitives where variants or
accessible overlay behavior are needed. Existing legacy CSS is migrated by
vertical screen slices and must not gain new module selectors.

