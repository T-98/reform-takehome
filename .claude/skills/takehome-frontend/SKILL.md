---
name: takehome-frontend
summary: Next.js App Router portal for 4h take-home. Option A UX. Declarative UI + minimal state + Suspense Query.
when_to_use:
  - building the portal UI
---

## Option A UX (required)
- One upload at a time.
- On file select/upload:
  - Show PDF immediately.
  - Right panel shows skeleton “Extracting…”
  - Disable upload until response completes (success/failure).
- After success:
  - Render extracted canonical fields + confidence badges
  - Render identifiers[] (“Other references found”)
  - Render tables[] (headers + rows with row/cell confidence)

## Data fetching (required)
Use TanStack Query with Suspense:
- Reads: useSuspenseQuery only if needed (Option A can be mostly mutation-driven)
- Upload/extract: useMutation
- Do not do fetch-in-useEffect for core server state

## State design (GreatFrontEnd distilled)
- Minimize local state: only file selection + current PDF URL + extracted result.
- Don’t store derived state; compute in render.
- Keep handlers small + named.

## UI states (graded)
- Idle (no file yet)
- Processing (skeleton + disabled upload)
- Success (data)
- Error (clear message + retry button)

## Required render sections
1) Canonical fields (nullable) with confidence
2) Identifiers list
3) Tables viewer (even if headers have no lines; you render what extraction returns)

## Output requirement
After UI changes, print:
- files changed
- local run steps
- manual test checklist (upload each sample doc; verify identifiers + tables)

## UI library (required)
Use shadcn/ui components for all standard UI:
- Layout: Card, Separator
- Inputs: Input, Label
- Actions: Button
- States: Skeleton, Alert
- Display: Badge, Table

Rules:
- Prefer shadcn components over custom HTML unless no equivalent exists.
- Tailwind is for layout (flex/grid/gap/padding), not rebuilding components.
- Skeletons must be shadcn Skeleton components in the extracted panel while processing.