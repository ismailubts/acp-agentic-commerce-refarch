# ACP Agentic Commerce Reference — Governed Agent Commerce

A hands-on reference build for autonomous shopping agents that stay inside explicit trust boundaries — with human approval where it matters.

Repository: acp-agentic-commerce-refarch

## Problem Statement

Most commerce stacks put every decision in one place. That works until an AI agent starts buying on someone's behalf. Then you need clear handoffs: what the agent may do alone, what needs a person, and what gets written down forever.

ACP Agentic Commerce Reference shows a practical pattern for **governed delegation** — agents shop within budgets and rules, merchants own checkout, humans approve risky spends, and every cross-boundary step lands in an audit trail.

## Architecture Overview

Six trust boundaries keep control visible:

1. **Buyer Intent** — Capture and validate what the human actually wants
2. **Buyer Agent** — Autonomous selection with hard constraint checks
3. **Merchant Checkout** — Catalog, pricing, and session ownership
4. **Human Approval** — Override path for high-risk purchases
5. **Mock Settlement** — Escrow-style payment simulation
6. **Audit Log** — Immutable event history

### Design Principles

- **Scoped authority** — Agents get limited power that can be revoked
- **Boundary isolation** — Each layer validates its own state
- **Human-in-the-loop** — High-risk paths require explicit approval
- **Audit by default** — Cross-boundary actions are recorded
- **Small surfaces** — Only the interfaces that are required

## Repository Structure

```
acp-agentic-commerce-refarch/
    README.md
    requirements.txt
    docs/
        architecture.md
        scenarios.md
        adrs/
            ADR-001-delegation-vs-custom-api.md
            ADR-002-human-approval-boundary.md
            ADR-003-mock-settlement-vs-real-payments.md
    diagrams/
        architecture.mmd
    data/
        products.json
    backend/
        app.py                         # Simple HTTP server (canonical)
        app_fastapi.py                 # FastAPI variant (deprecated)
        storage.py
        models/
            schemas.py
        agents/
            buyer_agent.py
            approval_agent.py
        merchant/
            catalog.py
            checkout_api.py
        settlement/
            escrow.py
    streamlit_app/
        app.py                         # Oversight UI
    tests/
        test_checkout_flow.py
        test_simple_flow.py
        test_streamlit_app.py
        test_ui_basic.py
```

## Setup and Run

### Prerequisites
- Python 3.14+
- Git

### Installation

```bash
git clone https://github.com/ismailubts/acp-agentic-commerce-refarch.git
cd acp-agentic-commerce-refarch

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Run

```bash
# Terminal 1 — API
python backend/app.py

# Terminal 2 — UI
python -m streamlit run streamlit_app/app.py
```

- API: http://localhost:8000  
- UI: http://localhost:8501  

### Tests

```bash
python tests/test_simple_flow.py
python tests/test_streamlit_app.py
python -m pytest tests/test_checkout_flow.py -q
```

## Demo Scenario

**"Buy a laptop bag under $120 with fast shipping"**

1. Enter the request in the ACP Agentic Commerce Reference UI
2. Agent picks **Executive Laptop Briefcase** ($119.99)
3. Approval gate fires (price over $100)
4. Approve or reject in the oversight panel
5. Complete checkout → mock settlement
6. Inspect the audit timeline

### Expected outcome

| Field | Value |
|---|---|
| Product | Executive Laptop Briefcase |
| Price | $119.99 |
| Approval | Required (>$100) |
| End state | Approved + settled |
| Audit | 5+ chronological events |

## Who this is for

- **Architects** — Trust-boundary patterns for agent commerce  
- **Product** — Where human approval helps vs. where it slows people down  
- **Security** — Clear threat surfaces and compliance-friendly trails  

## Known limitations

- Simple HTTP server is the supported entrypoint (Python 3.14 friendly)
- In-memory storage only
- Mock settlement — no live payments
- Single merchant, small catalog (8 SKUs)

## Roadmap

1. Multi-merchant federation  
2. Real payment + shipping adapters  
3. Richer multi-agent collaboration  
4. Multi-tenant / enterprise reporting  

## Architecture Decision Records

- [ADR-001](docs/adrs/ADR-001-delegation-vs-custom-api.md): Delegation-protocol principles vs custom API  
- [ADR-002](docs/adrs/ADR-002-human-approval-boundary.md): Human approval as a trust boundary  
- [ADR-003](docs/adrs/ADR-003-mock-settlement-vs-real-payments.md): Mock settlement strategy  

## Contributing

Keep the trust-boundary model intact. Autonomy is fine — as long as authority stays scoped and auditable.

## License

MIT — see `LICENSE`.

---

*ACP Agentic Commerce Reference is a teaching reference for governed agent commerce: autonomous where it is safe, human where it is not, and fully auditable either way.*
