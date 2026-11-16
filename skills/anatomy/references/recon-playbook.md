# Recon playbook

Techniques by input type. Use only what you are authorized to access; stop at login walls you have no account for and record them as unknowns.

## Live URL / web app
1. Fetch the home page and `robots.txt`, `sitemap.xml`, `/.well-known/`, `manifest.json`, `humans.txt`. Sitemaps reveal the route and content model.
2. Inspect HTML: framework markers (`__NEXT_DATA__`, `data-reactroot`, `ng-version`, `data-v-`, `astro-island`, `wp-content`), meta tags, preloaded fonts/scripts, analytics and chat widgets.
3. Response headers: `server`, `x-powered-by`, `via`, `cf-ray`, `x-vercel-id`, `set-cookie` names (session style), `content-security-policy` (lists third-party services), caching headers.
4. Network behavior (Playwright/browser devtools): record XHR/fetch, WebSocket and SSE traffic during a normal user journey. Note endpoint shapes, pagination style, error format, auth mechanism (cookie, bearer, OAuth), GraphQL vs. REST, realtime channels.
5. JS bundles: chunk names indicate routes and libraries; sourcemaps, if public, show module structure. Read for route tables, feature flags, API clients and state shape; do not copy code.
6. Walk the key flows manually: sign-up, core action, settings, billing, export, error states, empty states, mobile viewport. Screenshot at each step.
7. Public context: pricing/plan limits (reveal the data model and quotas), changelog, docs, status page, engineering blog, job posts.

## Local repo
1. Read README, manifests (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `pom.xml`), lockfiles.
2. Map the tree: entry points, routing, services, workers, shared libs.
3. Data: migrations, ORM models, schema files, seed data.
4. Config: env var names (not values), feature flags, Docker/compose, CI, IaC.
5. Tests and fixtures are executable documentation of behavior.
6. Check the license before characterizing reuse options.

## Docs / API spec / description only
1. Pull OpenAPI/GraphQL/Protobuf schemas and SDK references; derive entities and operations.
2. Read changelogs for how the product evolved; deprecations reveal past design mistakes.
3. Mark everything about internals as `[inferred]`; there is no direct evidence.

## CLI / binary / package
1. `--help` and every subcommand's help; man pages; shell completions.
2. Config locations and formats; files created; env vars read.
3. Contracts: stdin/stdout shapes, exit codes, machine-readable output flags.
4. Package metadata and dependency lists; `file`, `ldd`/`otool -L`, `strings` for linked libs and embedded URLs, only on binaries you have rights to inspect.
5. Observe behavior in a sandbox; record network calls and filesystem effects.

## Physical product (photos, measurements, spec sheets)
1. Collect what the user can supply: photos from several angles, caliper measurements, weight, material notes, spec sheets, manuals, teardown write-ups, regulatory filings (e.g. FCC internal photos), parts lists.
2. Identify subsystems (structure, mechanism, electronics, power, interface) and how they connect.
3. Record each dimension with its source tag. Ask for missing critical measurements instead of guessing; mark unavoidable guesses `[assumed]`.
4. Note materials, manufacturing method hints (injection molding parting lines, fasteners, seams) and tolerances that matter for fit.
