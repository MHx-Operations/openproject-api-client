---
created: 2026-05-13T07:05:39.526Z
completed: 2026-05-13
title: Update GitHub Actions to Node.js 24 compatible versions
area: tooling
files:
  - .github/workflows/ci.yml:17,20
  - .github/workflows/publish.yml:16,19,34,37,65,84
resolution: Merged in commit c5afbae (checkout v6, setup-python v6, upload-artifact v7, download-artifact v8)
---

## Problem

GitHub Actions pipeline emits deprecation warning: Node.js 20 actions are
deprecated. From June 2nd, 2026 actions will be forced to run on Node.js 24
by default; Node.js 20 is removed from the runner on September 16th, 2026.

Affected actions currently pinned in this repo:
- `actions/checkout@v4` — ci.yml:17, publish.yml:16, publish.yml:34
- `actions/setup-python@v5` — ci.yml:20, publish.yml:19, publish.yml:37
- `actions/upload-artifact@v4` — publish.yml:65
- `actions/download-artifact@v4` — publish.yml:84

Reference: https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/

## Solution

Check upstream for Node.js 24-compatible major versions of each action and
bump pins (likely `actions/checkout@v5`, `actions/setup-python@v6`, etc. —
verify on the action repos before changing). Run CI to confirm no warnings.

Interim opt-in (if we want to validate before June 2026 default switch):
set `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` as a workflow env var.

Deadline: complete well before 2026-09-16 (runner removal of Node.js 20).
