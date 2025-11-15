"""
In-memory storage layer for the BoundCart governed agent commerce reference.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from backend.models.schemas import (
    Product,
    CheckoutSession,
    ApprovalDecision,
    SettlementEvent,
    AuditEvent,
    CheckoutStatus,
    ApprovalStatus,
    AuditEventType,
)


class InMemoryStorage:
    """Centralized in-memory storage for all application data."""
    
    def __init__(self):
        """Initialize storage with empty collections."""
        # Product catalog
        self.products: Dict[str, Product] = {}
        
        # Checkout sessions
        self.checkout_sessions: Dict[str, CheckoutSession] = {}
        
        # Approval decisions
        self.approvals: Dict[str, ApprovalDecision] = {}
        
        # Settlement events
        self.settlements: Dict[str, SettlementEvent] = {}
        
        # Audit events (list for chronological ordering)
        self.audit_events: List[AuditEvent] = []
        
        # Counters for ID generation
        self._session_counter = 1000
        self._settlement_counter = 5000
        self._audit_counter = 9000
    
    def generate_session_id(self) -> str:
        """Generate a unique session ID."""
        self._session_counter += 1
        return f"session_{self._session_counter}"
    
    def generate_settlement_id(self) -> str:
        """Generate a unique settlement ID."""
        self._settlement_counter += 1
        return f"settlement_{self._settlement_counter}"
    
    def generate_audit_id(self) -> str:
        """Generate a unique audit event ID."""
        self._audit_counter += 1
        return f"audit_{self._audit_counter}"
    
    # Product operations
    def add_product(self, product: Product) -> None:
        """Add a product to the catalog."""
        self.products[product.id] = product
    
    def get_product(self, product_id: str) -> Optional[Product]:
        """Get a product by ID."""
        return self.products.get(product_id)
    
    def get_all_products(self) -> List[Product]:
        """Get all products."""
        return list(self.products.values())
    
    # Checkout session operations
    def add_checkout_session(self, session: CheckoutSession) -> None:
        """Add a checkout session."""
        self.checkout_sessions[session.session_id] = session
    
    def get_checkout_session(self, session_id: str) -> Optional[CheckoutSession]:
        """Get a checkout session by ID."""
        return self.checkout_sessions.get(session_id)
    
    def update_checkout_session(self, session: CheckoutSession) -> None:
        """Update a checkout session."""
        if session.session_id in self.checkout_sessions:
            self.checkout_sessions[session.session_id] = session
    
    # Approval operations
    def add_approval(self, approval: ApprovalDecision) -> None:
        """Add an approval decision."""
        self.approvals[approval.session_id] = approval
    
    def get_approval(self, session_id: str) -> Optional[ApprovalDecision]:
        """Get approval decision by session ID."""
        return self.approvals.get(session_id)
    
    # Settlement operations
    def add_settlement(self, settlement: SettlementEvent) -> None:
        """Add a settlement event."""
        self.settlements[settlement.settlement_id] = settlement
    
    def get_settlement(self, settlement_id: str) -> Optional[SettlementEvent]:
        """Get settlement event by ID."""
        return self.settlements.get(settlement_id)
    
    def get_settlement_by_session(self, session_id: str) -> Optional[SettlementEvent]:
        """Get settlement event by session ID."""
        for settlement in self.settlements.values():
            if settlement.session_id == session_id:
                return settlement
        return None
    
    # Audit operations
    def add_audit_event(self, event: AuditEvent) -> None:
        """Add an audit event."""
        self.audit_events.append(event)
    
    def get_audit_events(self, session_id: Optional[str] = None) -> List[AuditEvent]:
        """Get audit events, optionally filtered by session ID."""
        if session_id:
            return [event for event in self.audit_events if event.session_id == session_id]
        return self.audit_events.copy()
    
    def get_audit_events_for_session(self, session_id: str) -> List[AuditEvent]:
        """Get audit events for a specific session."""
        return [event for event in self.audit_events if event.session_id == session_id]
    
    # Approval operations
    def get_pending_approvals(self) -> List:
        """Get all pending approval requests."""
        # For this simple implementation, return mock pending approvals
        pending = []
        for session in self.checkout_sessions.values():
            if session.approval_status == ApprovalStatus.PENDING:
                approval = {
                    "approval_id": f"approval_{session.session_id}",
                    "session_id": session.session_id,
                    "status": "pending",
                    "total_amount": session.total,
                    "product_name": session.line_item.product_name if session.line_item else "Unknown Product",
                    "risk_factors": session.approval_risk_factors or [],
                    "created_at": session.created_at,
                    "expires_at": None
                }
                pending.append(approval)
        return pending
    
    # Utility methods
    def create_audit_event(
        self,
        event_type: AuditEventType,
        session_id: Optional[str] = None,
        actor: str = "system",
        details: Optional[Dict] = None
    ) -> AuditEvent:
        """Create and store an audit event."""
        event = AuditEvent(
            event_id=self.generate_audit_id(),
            event_type=event_type,
            session_id=session_id,
            timestamp=datetime.now(),
            actor=actor,
            details=details or {}
        )
        self.add_audit_event(event)
        return event


# Global storage instance
storage = InMemoryStorage()
