# Stack inference signals

Give each guess a confidence (high / medium / low) and list the signals. Multiple independent signals raise confidence; a single header does not.

| Layer | Signals |
|---|---|
| Frontend framework | `__NEXT_DATA__`, `_next/` (Next.js); `__NUXT__` (Nuxt); `ng-version` (Angular); `data-v-` attrs (Vue); `astro-island` (Astro); `data-sveltekit` (SvelteKit); hydration markers; chunk naming |
| Styling | Utility class patterns (Tailwind), CSS-in-JS class hashes, Bootstrap/Material class names, design-token CSS variables |
| State / data fetching | Network shapes: GraphQL (`/graphql`, persisted queries), tRPC (`/trpc`), REST JSON:API, RSC payloads, SWR/React Query cache behavior |
| Backend | Error page styles, cookie names (`connect.sid`, `_rails`, `laravel_session`, `csrftoken`), header hints, API error formats, stack traces |
| Hosting / edge | `cf-ray` (Cloudflare), `x-vercel-id`, `x-amz-*`/`x-amz-cf-id` (AWS/CloudFront), `fly-request-id`, `x-nf-request-id` (Netlify), DNS CNAMEs |
| Auth | Cookie vs. bearer, OAuth redirect hosts (Auth0, Clerk, Cognito, Okta, Supabase), JWT claims shape |
| Realtime | WebSocket URLs and frame shapes, SSE, Socket.IO handshake, Pusher/Ably/PartyKit hosts |
| Data stores (inferred) | ID formats (UUID v4/v7, ULID, Mongo ObjectId, sequential ints), pagination style (cursor vs. offset), search behavior, feature hints in pricing |
| Payments / email / analytics | Stripe/Paddle JS, Segment/PostHog/Amplitude, Intercom, SendGrid/Postmark links, CSP allowlists |
| Mobile | Bundle/package metadata, React Native/Flutter markers, store listings, deep link schemes |
| Hiring signal | Job postings and engineering blog posts often name the real stack; treat as `[documented]` for the company, `[inferred]` for this product |

Never present a store or language as certain unless it was read from source or official docs.
