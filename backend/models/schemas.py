"""
Simple models and enums for the BoundCart governed agent commerce reference.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any


class CheckoutStatus:
    """Checkout session status."""
    CREATED = "created"
    PENDING_PAYMENT = "pending_payment"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ApprovalStatus:
    """Approval status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NOT_REQUIRED = "not_required"


class SettlementStatus:
    """Settlement status."""
    CREATED = "created"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AuditEventType:
    """Audit event types."""
    SESSION_CREATED = "session_created"
    PRODUCTS_SHORTLISTED = "products_shortlisted"
    PRODUCT_SELECTED = "product_selected"
    CHECKOUT_SESSION_CREATED = "checkout_session_created"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_REJECTED = "approval_rejected"
    CHECKOUT_COMPLETED = "checkout_completed"
    SETTLEMENT_INITIATED = "settlement_initiated"
    SETTLEMENT_COMPLETED = "settlement_completed"


class Product:
    """Product model."""
    def __init__(self, id: str, name: str, category: str, price: float, 
                 shipping_eta_days: int, inventory: int, short_description: str):
        self.id = id
        self.name = name
        self.category = category
        self.price = price
        self.shipping_eta_days = shipping_eta_days
        self.inventory = inventory
        self.short_description = short_description


class BuyerIntent:
    """Buyer intent capturing user requirements and constraints."""
    def __init__(self, max_price: Optional[float] = None, category: Optional[str] = None,
                 max_shipping_days: Optional[int] = None, min_rating: Optional[float] = None,
                 special_requirements: Optional[str] = None):
        self.max_price = max_price
        self.category = category
        self.max_shipping_days = max_shipping_days
        self.min_rating = min_rating
        self.special_requirements = special_requirements


class LineItem:
    """Line item in a checkout session."""
    def __init__(self, product_id: str, product_name: str, quantity: int,
                 unit_price: float, total_price: float):
        self.product_id = product_id
        self.product_name = product_name
        self.quantity = quantity
        self.unit_price = unit_price
        self.total_price = total_price


class ShippingOption:
    """Shipping option for checkout."""
    def __init__(self, method: str, eta_days: int, cost: float):
        self.method = method
        self.eta_days = eta_days
        self.cost = cost


class CheckoutSession:
    """Checkout session model."""
    def __init__(self, session_id: str, line_item: LineItem, shipping_option: ShippingOption,
                 subtotal: float, tax: float, total: float, checkout_status: str,
                 approval_status: str, created_at: datetime, updated_at: datetime,
                 approval_risk_factors: Optional[List[str]] = None):
        self.session_id = session_id
        self.line_item = line_item
        self.shipping_option = shipping_option
        self.subtotal = subtotal
        self.tax = tax
        self.total = total
        self.checkout_status = checkout_status
        self.approval_status = approval_status
        self.created_at = created_at
        self.updated_at = updated_at
        self.approval_risk_factors = approval_risk_factors


class CheckoutRequest:
    """Request to create checkout session."""
    def __init__(self, product_id: str, quantity: int, buyer_intent: BuyerIntent):
        self.product_id = product_id
        self.quantity = quantity
        self.buyer_intent = buyer_intent


class CheckoutResponse:
    """Response from checkout session creation."""
    def __init__(self, session: CheckoutSession, requires_approval: bool,
                 approval_risk_factors: Optional[List[str]] = None):
        self.session = session
        self.requires_approval = requires_approval
        self.approval_risk_factors = approval_risk_factors


class ApprovalRequest:
    """Approval request."""
    def __init__(self, session_id: str, approver: str, decision: str, rationale: str):
        self.session_id = session_id
        self.approver = approver
        self.decision = decision
        self.rationale = rationale


class ApprovalDecision:
    """Approval decision model."""
    def __init__(self, session_id: str, approver: str, decision: str, rationale: str, timestamp: datetime):
        self.session_id = session_id
        self.approver = approver
        self.decision = decision
        self.rationale = rationale
        self.timestamp = timestamp


class SessionUpdateRequest:
    """Request to update checkout session."""
    def __init__(self, quantity: Optional[int] = None, shipping_method: Optional[str] = None):
        self.quantity = quantity
        self.shipping_method = shipping_method


class SettlementEvent:
    """Settlement event model."""
    def __init__(self, settlement_id: str, session_id: str, amount: float, status: str,
                 provider: str, created_at: datetime, completed_at: Optional[datetime] = None,
                 transaction_id: Optional[str] = None):
        self.settlement_id = settlement_id
        self.session_id = session_id
        self.amount = amount
        self.status = status
        self.provider = provider
        self.created_at = created_at
        self.completed_at = completed_at
        self.transaction_id = transaction_id


class AuditEvent:
    """Audit event model."""
    def __init__(self, event_id: str, event_type: str, actor: str, timestamp: datetime,
                 session_id: Optional[str] = None, approval_id: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        self.event_id = event_id
        self.event_type = event_type
        self.actor = actor
        self.timestamp = timestamp
        self.session_id = session_id
        self.approval_id = approval_id
        self.details = details


