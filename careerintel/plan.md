# Implementation plan — Placement Intelligence

## Scope and project facts

The supplied brief requests a complete frontend/UI and frontend integration for an existing Placement Prediction & Skill Gap Analyzer. The current WebDev project directory `/home/ubuntu/careerintel` is empty apart from Git metadata. The only supplied artifact is the written brief; no application source, backend code, OpenAPI document, API base URL, or model artifacts are present. Therefore, the existing endpoints, input/output schemas, functions, and model outputs cannot yet be inspected, and no endpoint names or response formats will be assumed.

This is a frontend-only project. The app will not recreate ML, readiness, role-gap, recommendations, salary, EDA, or what-if logic. It will not seed demo students, dashboard totals, predictions, chart points, skill values, or performance metrics. Data-dependent views will stay in honest loading, not-connected, unavailable, or retryable error states until real backend data arrives.

To make the frontend usable without guessing the missing API, the proposed integration boundary is a configurable, OpenAPI-assisted browser client: connect to an API base URL and OpenAPI document, discover operations from that document, then bind the discovered operations and their schemas to the product capabilities. Capability results remain the backend's actual JSON; UI display rules will map only fields supported by the documented/observed response, and unavailable measures remain absent. If the backend lacks OpenAPI, its source code or a documented endpoint/input/output contract is required before final endpoint-specific bindings can be completed. The browser client will surface CORS/auth/network failures clearly; no private backend credentials will be put in app source or silently persisted.

## Implementation approach

- Build a responsive React + TypeScript single-page application using Vite, React Router, reusable UI components, and a charting library for real backend-supplied series only.
- Keep selected-student identity and fetched capability results in shared app state across all routes. Do not refresh the whole app when switching students.
- Organize the application around the nine requested destinations: Overview, Student Profile, Placement Prediction, Skill Gap Analysis, Recommendations, Salary Prediction, What-If Analysis, Data Analysis / EDA, and Model Performance. Add a compact connection/settings entry point for backend setup, since the actual contract is not present.
- Implement an API connection layer that loads the supplied OpenAPI document, presents discovered operations/schemas, allows capability-to-operation bindings, sends only schema-backed/profile-backed requests, and retains raw JSON for traceable field mapping. Keep endpoint-specific bindings isolated from presentation components so the true backend contract can replace initial configuration without rewriting pages.
- Use explicit component states: not connected/no selected student, loading, loaded, unavailable, and retryable error. Keep the selected profile when navigation or requests fail. Never substitute sample values for missing results.
- Keep computed calculations in backend operations. Frontend transformations are limited to formatting, grouping actual returned items, and rendering already returned values.
- Do not enable a managed server or database: no application-owned backend or persistence was requested. API connectivity will be browser-side and must respect the actual backend's CORS/auth configuration.
- Provide a route manifest at `public/manus-routes.json`, keep it synchronized with route definitions, and expose the project through the managed live Preview. Publication is not in scope unless separately requested.

## Requested product behavior

### Overview and student flow

Show project identity and concise system purpose, a student search/selector, selected-student summary, actual placement probability, readiness score, target role, returned strengths and gaps, recommendation count, and salary only when the service returns valid data. Provide direct actions to load/rerun analysis and navigate into the relevant analysis. Generic aggregate platform statistics are excluded unless returned/calculated from the backend dataset.

Student selection supports search, basic information, selecting/loading another student without a full refresh, and retaining selection across pages. If the actual backend supports new profile creation, present schema-backed inputs in sections: Academic (CGPA, backlogs, attendance, other available academic fields); Experience (internships, projects, certifications and relevant experience); Technical Skills (programming, DSA, SQL, web development, cloud and other available fields); Aptitude & Soft Skills; Career Target (target role). Do not invent fields unsupported by the actual schema.

### Analysis destinations

- **Student Profile:** Academic, technical, experience, aptitude, communication and career-target sections; useful skill levels, academic metrics, experience indicators and completeness only where derivable from returned profile data; a visible run/rerun action.
- **Placement Prediction:** Actual prediction/result and probability; risk interpretation and confidence only when defined by the backend; model identity, timestamp and profile basis where supplied; backend/explainability-derived positive and negative contributing factors; a clear non-guarantee statement.
- **Skill Gap Analysis:** Role selector populated from actual backend role requirements; current and required skill level, difference/gap, importance and status for each returned skill; strong/adequate/improve/critical states and role fit only where generated by backend logic. Role changes request/re-render the corresponding backend analysis.
- **Skill comparison visualization:** Compare the selected student's actual values with actual target-role requirements using accessible bars/matrix and priority indicators; no hardcoded chart values.
- **Recommendations:** Only engine-generated recommendations, grouped by returned priority; show area, current/required/gap/priority, reason, action and expected impact when provided.
- **What-If Analysis:** Let the student adjust only schema-supported skill inputs and submit changes to the existing backend operation; show original/updated probability, delta, changed skills and per-skill effects only when returned by the model. Never reproduce the model calculation in the browser.
- **Salary Prediction:** Show salary/package, range, factors, model and interpretation only when the selected student's backend response has a valid prediction; otherwise show an unavailable state. Do not describe a prediction as guaranteed.
- **Data Analysis / EDA:** Render actual dataset records/features, target distribution, missing values, dtypes, distributions, relationships/correlations and insights only when returned/generated by project analysis; interactive charts are used where the backend supplies suitable series.
- **Model Performance:** Render available classification accuracy/precision/recall/F1/ROC-AUC, regression MAE/RMSE/R², model comparison, confusion matrix, ROC, calibration and feature/permutation importance only from actual model artifacts/results.

### Shared behavior and trust

Every data-dependent page has loading, no-data/no-student and error states. API/model failures use plain user-facing explanations and retry controls; raw exceptions/stack traces are not shown. Where available, show model, timestamp, current-profile basis, and whether a result is a model prediction or a requirement-based result. Keep ML placement probability distinct from placement readiness score and skill-gap analysis. UI copy must not imply placement or salary guarantees. Components are reusable for selectors, metrics, skill bars, prediction result, recommendations, gaps, comparisons, model metrics, empty/loading/error states, tables, filters and section headers. Layout works at desktop, laptop and tablet widths.

## Design system

- **Design movement:** Editorial decision-intelligence software: a disciplined data terminal softened with an editorial reading rhythm, rather than a stock college-admin template.
- **Core principles:** (1) evidence before decoration; (2) one clear focal result per page; (3) show provenance and uncertainty beside predictions; (4) progressive disclosure for dense model detail.
- **Color philosophy:** Warm near-white canvas and graphite/ink text support long analytical sessions; a precise teal signals active analysis and positive evidence; amber and restrained coral are reserved for risk/gaps and never used as decorative alarm. Neutral chart tracks keep returned model outputs legible. **Signature brand color:** deep mineral teal `#0B8F83`.
- **Layout paradigm:** Persistent narrow navigation rail plus an anchored student context strip and wide, asymmetrical analysis canvas; narrative lead-in, primary evidence panel and supporting evidence rail, with responsive stacking on tablet. Avoid a centered generic KPI-card grid.
- **Signature elements:** a custom monogram/trajectory mark; fine ruled section dividers with small numbered evidence labels; compact provenance chips for model/time/source.
- **Interaction philosophy:** Direct manipulation for student/role/what-if controls, with explicit loading and result-delta feedback. No selection should silently change another student's data; persistent context makes the analyzed subject visible.
- **Animation:** Subtle 140–200 ms opacity/position transitions for route and control state changes; animated chart entrances only for returned values; honor reduced-motion preferences; no looping decoration or fake “live” activity.
- **Typography system:** Space Grotesk for headings and UI labels; IBM Plex Sans for readable analytical copy; IBM Plex Mono for model IDs, metrics, timestamps and numeric deltas. Tabular numerals for aligned values; strong size contrast without oversized marketing headings.
- **Brand essence:** A transparent career-readiness intelligence workspace for students and advisors that explains what the selected student's real profile and models say—and where the evidence came from. Personality: rigorous, candid, actionable.
- **Brand voice:** Clear, analytical, non-promissory; headlines explain the question answered and CTAs use direct verbs. Examples: “What is shaping this placement estimate?” and “Run analysis for this profile”.
- **Wordmark & logo:** A custom “PI” mark built from two offset vertical bars joined by an upward path, paired with the Placement Intelligence wordmark; create as a small SVG, not plain default-font text.

## Project structure

```text
/home/ubuntu/careerintel/
├── plan.md
├── TODO.md                         # native todo is not available; fallback after plan approval
├── app.config.ts                   # project logo URL metadata
├── package.json                    # pinned dependencies and scripts
├── pnpm-lock.yaml                  # reproducible dependency resolution
├── pnpm-workspace.yaml             # reviewed lifecycle-script policy
├── index.html
├── public/
│   ├── manus-routes.json           # route manifest required by WebDev
│   └── logo.svg
└── src/
    ├── main.tsx                    # Vite bootstrap
    ├── App.tsx                     # routes for the nine product pages plus connection settings
    ├── app/AppContext.tsx          # student, role, API settings, capability results and request state
    ├── api/                        # OpenAPI discovery, browser transport, safe errors and field mapping
    ├── components/                 # shell, reusable UI states, schema form and lazy-loaded charts
    ├── pages/                      # analysis destinations and backend connection configuration
    ├── types.ts                    # capability, connection, operation and result contracts
    └── styles.css                  # design tokens, typography and responsive component styling
```

## Dependencies and serving

Use a pinned `pnpm` toolchain, React, TypeScript, Vite, React Router, a restrained icon package, and a chart library only where appropriate. Pin versions in the lockfile and explicitly review pnpm lifecycle-script permissions before dependency installation. The frontend is served on the project's configured port 3000 and consumes the existing backend from the browser; no ML/backend code is changed. Do not claim verified API integration until the actual service source/spec is supplied and the discovered bindings are confirmed. The project remains Preview-only for this task; `publishing.auto_publish` is false and no public publication is planned.

## Accepted decisions and remaining integration input

1. The user approved this scope and implementation approach (“yes go on”). The interface is implemented as a configurable, honest frontend; no endpoint-specific model logic is recreated.
2. Verified integration with the actual backend remains open: provide the existing project source/repository or backend API base URL plus OpenAPI/Swagger document (or endpoint documentation with example inputs/outputs). The supplied workspace contained no backend source or API schema, so API operations, response mappings and model outputs remain unverified. The user-approved fallback is to keep data views empty until real operations and responses are configured; do not show demo data or claim integration is complete.
