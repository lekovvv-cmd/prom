# Frontend architecture

`apps/platform-shell` owns global providers, platform routes, error/loading
states, and the module registry. Product manifests live in their product
directories and are loaded with `React.lazy`; the shell never eagerly imports
module pages. Generic transport has no product side effects. Query state belongs
to module-scoped query-key factories.

Tailwind 4.3.3 is integrated through the official Vite plugin. New shared UI
uses semantic tokens and CVA variants. Dialog, Popover, Tabs, Select,
Dropdown, Tooltip, Checkbox, Switch, and the searchable combobox use Radix
Primitives for focus, keyboard, dismissal, and ARIA behavior. The platform
global stylesheet contains only Tailwind import, tokens, reset, and base
typography. Shared UI and layout styles live with their packages; product
selectors live only in the owning module.

The style gate enforces source-size budgets and rejects component or product
selectors in the global layer. Bundle checks separately cap initial JavaScript,
initial CSS, the largest lazy JavaScript chunk, and the largest lazy CSS chunk.
CSS Modules remain reserved for genuinely complex local layout or interaction
cases; shared visual patterns belong in `@prom/ui`.
