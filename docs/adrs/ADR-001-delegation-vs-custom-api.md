# ADR-001: Delegation Principles vs Custom API Approach

## Status
Accepted

## Context
BoundCart needs to show how autonomous commerce can keep humans in control while still letting agents shop. The choice is between adopting established **governed-delegation / trust-boundary** principles versus inventing a wholly custom API with no shared vocabulary.

## Decision
Adopt a **delegation-inspired approach**: implement controlled authority, trust boundaries, and auditability — without attempting a full industry protocol stack.

## Rationale

### Why delegation-inspired

1. **Trust boundary design** — Clear seams between human intent, agent decisioning, merchant checkout, approval, settlement, and audit.
2. **Controlled delegation** — Agents operate with explicit authority limits and revocation.
3. **Audit-first** — Cross-boundary actions are recorded for compliance and forensics.
4. **Teaching value** — Patterns transfer to other human–agent domains.
5. **Practical scope** — Enough structure to learn from, without protocol theater.

### Why not a full protocol implementation

1. Protocol complexity distracts from architectural learning goals.
2. This is a reference build, not a production standards compliance project.
3. Timeline and mock services make full protocol work low value here.
4. The teaching target is boundary design, not wire-format compliance.

### What BoundCart implements

**Principles**
1. Explicit delegation scopes
2. Six trust boundaries with validation
3. Human-in-the-loop for high-risk paths
4. Immutable audit events
5. Human override / revocation

**Patterns**
1. Boundary controllers
2. Validated state transitions
3. Event-sourced audit trail
4. Agent-as-proxy with limited authority
5. Approval workflows

**Out of scope**
1. Full message formats / transport stacks
2. Protocol-specific cryptography
3. Multi-party agent negotiation
4. Cross-org federation protocols
5. Dynamic discovery networks

## Consequences

### Positive
- Clear, teachable architecture
- Transferable patterns
- Complexity matched to reference scope
- Room to deepen later

### Negative
- Not a standards-compliant protocol client
- Mock security surfaces
- Single-merchant demo scope

### Mitigations
- Document inspiration vs full compliance clearly
- Keep extension points for later protocol work
- Emphasize patterns over protocol fidelity

## Alternatives considered

### 1. Pure custom API
Maximum flexibility, but reinvented patterns and weaker teaching value. **Rejected.**

### 2. Full protocol compliance
Highest fidelity, excessive complexity for a reference. **Rejected.**

### 3. Ad-hoc hybrid
Mixes vocabularies and muddies learning goals. **Rejected.**

## Implementation notes

1. **Foundation** — Boundaries, delegation, audit log  
2. **Agent integration** — Buyer agent + approval gates  
3. **Control** — Human override and richer compliance views  

## Future path

Optional later work: richer message contracts, stronger crypto, federation, discovery — only if BoundCart grows beyond a teaching reference.

---

*This decision favors clear governed-delegation patterns over protocol completeness.*
