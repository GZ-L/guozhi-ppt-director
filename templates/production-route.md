# Production Route

Machine source of truth: `run-manifest.json`

## Route Decision

- Protocol version:
- Request ID:
- Run ID:
- Route ID: native_pptx / web_deck / dual / dashiai / review_only
- Confirmed deliverable:
- Editability requirement:
- Motion requirement:
- Capability check:
- Capability version:
- Capability status: available / missing / unverified
- Route confidence: high / medium / low

## Renderer Boundary

- Renderer or tool:
- Capability role: renderer
- Director decisions delegated: none
- Input package:
- Output directory:
- Temporary render directory:

## External Renderer Fields

- DashiAI project path, when route is `dashiai`:
- DashiAI theme:
- DashiAI goal path:
- DashiAI media intent:

## Expected Outputs

- Requested artifacts:
- Renderer outputs:
- Final checked artifacts:

## Verification Plan

- Confirm manifest state is `planned` before rendering.
- Confirm output paths are under the current run directory.
- Run renderer-specific validation and visual QA.
- Record command, result, and evidence for every capability check.

## Failure Behavior

- Missing capability status: blocked
- Render or validation failure status: failed
- Route changes require explicit approval; no silent fallback.
