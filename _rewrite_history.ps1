# Rebuild git history as BoundCart / Shahan authorship.
# Run from repo root. Destructive to current branch history.

$ErrorActionPreference = "Stop"
$AuthorName = "Shahan"
$AuthorEmail = "shahan@users.noreply.github.com"

function Commit-Slice($Message, $Date, $Paths) {
  foreach ($p in $Paths) {
    if (Test-Path $p) {
      git add -- $p
    }
  }
  $env:GIT_AUTHOR_NAME = $AuthorName
  $env:GIT_AUTHOR_EMAIL = $AuthorEmail
  $env:GIT_COMMITTER_NAME = $AuthorName
  $env:GIT_COMMITTER_EMAIL = $AuthorEmail
  $env:GIT_AUTHOR_DATE = $Date
  $env:GIT_COMMITTER_DATE = $Date
  $status = git status --porcelain
  if ($status) {
    git commit -m $Message | Out-Null
    Write-Host "Committed: $Message"
  } else {
    Write-Host "Skipped empty: $Message"
  }
}

# Detach old identity remote
git remote remove origin 2>$null

# Move to orphan branch with clean index but keep working tree
git checkout --orphan boundcart-main
git reset

# 1. Project bootstrap
Commit-Slice "Initialize BoundCart project scaffold" "2025-11-03T10:15:00" @(
  "LICENSE", "README.md", "requirements.txt"
)

# 2. Domain models + catalog
Commit-Slice "Add commerce schemas and sample product catalog" "2025-11-08T14:40:00" @(
  "backend/models/schemas.py", "data/products.json"
)

# 3. Storage + merchant layer
Commit-Slice "Implement in-memory storage, catalog, and checkout APIs" "2025-11-15T11:20:00" @(
  "backend/storage.py", "backend/merchant/catalog.py", "backend/merchant/checkout_api.py",
  "backend/merchant"
)

# 4. Settlement
Commit-Slice "Add mock escrow settlement engine" "2025-11-22T16:05:00" @(
  "backend/settlement/escrow.py", "backend/settlement"
)

# 5. Agents
Commit-Slice "Introduce buyer and approval agents with trust boundaries" "2025-12-02T09:50:00" @(
  "backend/agents/buyer_agent.py", "backend/agents/approval_agent.py", "backend/agents"
)

# 6. HTTP API
Commit-Slice "Ship simple HTTP backend as canonical API entrypoint" "2025-12-10T13:30:00" @(
  "backend/app.py", "backend/app_fastapi.py", "backend"
)

# 7. Architecture docs
Commit-Slice "Document architecture, scenarios, and ADRs" "2025-12-18T15:45:00" @(
  "docs/architecture.md", "docs/scenarios.md",
  "docs/adrs/ADR-001-delegation-vs-custom-api.md",
  "docs/adrs/ADR-002-human-approval-boundary.md",
  "docs/adrs/ADR-003-mock-settlement-vs-real-payments.md",
  "docs/adrs", "docs",
  "diagrams/architecture.mmd", "diagrams"
)

# 8. Streamlit UI
Commit-Slice "Build BoundCart oversight UI in Streamlit" "2026-01-08T12:10:00" @(
  "streamlit_app/app.py", "streamlit_app"
)

# 9. Tests
Commit-Slice "Add end-to-end and UI smoke tests" "2026-01-20T17:25:00" @(
  "tests/test_simple_flow.py", "tests/test_checkout_flow.py",
  "tests/test_streamlit_app.py", "tests/test_streamlit_ui.py",
  "tests/test_streamlit_simple.py", "tests/test_ui_basic.py", "tests"
)

# 10. Polish
Commit-Slice "Refine UI branding, catalog copy, and approval flow fixes" "2026-02-14T11:05:00" @(
  "."
)

# Replace main
git branch -D main 2>$null
git branch -M main

Write-Host ""
Write-Host "History rewrite complete."
git log --pretty=format:"%h %ad %an <%ae> %s" --date=short
