# Blueprint template

Output folder `anatomy-<product-slug>/`. Standard depth uses all files; scale down for quick passes.

```
00-overview.md        purpose, users, business model, scope of analysis, confidence summary, reading guide
10-features.md        feature inventory (core / supporting / incidental), each with evidence tag
20-ux-flows.md        key journeys, screens/states, edge cases; Mermaid flowcharts
30-architecture.md    components, boundaries, sync/async, realtime, third parties; Mermaid diagram
40-data-model.md      entities, fields, relationships, lifecycle, tenancy; Mermaid ER diagram
50-interfaces.md      public/internal APIs, events, auth and permissions model
60-tech-stack.md      inferred stack table: layer, guess, confidence, signals
70-nonfunctional.md   performance, scale hints, security, accessibility, i18n, offline
80-gaps-and-risks.md  unknowns, assumptions, legal & IP notes, ToS constraints
90-rebuild-spec.md    the actionable build plan (below)
evidence-log.md       sources consulted and what each showed
prototype/            demo build, viewer.html, STL + renders, or drawings, with README (see prototype-phase.md)
```

## Per-feature entry (10-features.md)
- Name, one-line purpose, priority (core / supporting / incidental)
- Behavior (rules, limits, states), evidence tag
- Dependencies (data, services, other features)

## Rebuild spec (90-rebuild-spec.md)
1. **Goal and scope**: faithful clone vs. improved; in/out of scope
2. **Recommended stack**: choices with reasons, and divergences from the original
3. **Module breakdown**: responsibilities and interfaces between modules
4. **Data schema draft**: tables/collections with key fields and indexes
5. **API surface**: endpoints or commands with request/response sketches
6. **Phased plan**: MVP, parity, polish; each phase with exit criteria
7. **Acceptance criteria**: testable statements per core feature
8. **Prototype scope**: which mode (build demo, viewer, 3D print, drawings) and which acceptance criteria it should demonstrate
9. **Risks and open questions**: what must be resolved before or during the build
10. **Improvements over the original**: weaknesses observed and proposed fixes
