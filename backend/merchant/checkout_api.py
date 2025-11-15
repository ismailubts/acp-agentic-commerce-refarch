"""
Checkout API for managing checkout sessions in the BoundCart governed agent commerce reference.
"""

from datetime import datetime
from typing import Optional, List

from ..models.schemas import (
    CheckoutSession,
    CheckoutRequest,
    CheckoutResponse,
    LineItem,
    ShippingOption,
    CheckoutStatus,
    ApprovalStatus,
    Product
)
from ..storage import storage
from .catalog import catalog_manager


class CheckoutManager:
    """Manages checkout session lifecycle."""
    
    def __init__(self):
        """Initialize checkout manager."""
        self.shipping_options = {
            "standard": {"method": "standard", "eta_days": 7, "cost": 5.99},
            "express": {"method": "express", "eta_days": 3, "cost": 12.99},
            "overnight": {"method": "overnight", "eta_days": 1, "cost": 24.99}
        }
    
    def create_checkout_session(self, request: CheckoutRequest) -> CheckoutResponse:
        """
        Create a new checkout session.
        
        Args:
            request: Checkout request with product and quantity
            
        Returns:
            CheckoutResponse: Created session with approval requirements
        """
        # Validate product exists and is available
        product = catalog_manager.get_product_by_id(request.product_id)
        if not product:
            raise ValueError(f"Product not found: {request.product_id}")
        
        if not catalog_manager.check_availability(request.product_id, request.quantity):
            raise ValueError(f"Insufficient inventory for product: {request.product_id}")
        
        # Create line item
        line_item = LineItem(
            product_id=product.id,
            product_name=product.name,
            quantity=request.quantity,
            unit_price=product.price,
            total_price=product.price * request.quantity
        )
        
        # Determine shipping option (default to express for demo)
        shipping_method = "express"  # Could be based on buyer intent
        shipping_config = self.shipping_options[shipping_method]
        shipping_option = ShippingOption(**shipping_config)
        
        # Calculate totals
        subtotal = line_item.total_price
        tax = subtotal * 0.08  # 8% tax (mock)
        total = subtotal + tax + shipping_option.cost
        
        # Create session
        session_id = storage.generate_session_id()
        session = CheckoutSession(
            session_id=session_id,
            line_item=line_item,
            shipping_option=shipping_option,
            subtotal=subtotal,
            tax=tax,
            total=total,
            checkout_status=CheckoutStatus.CREATED,
            approval_status=ApprovalStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Determine if approval is required
        approval_decision = self._assess_approval_requirement(session, request.buyer_intent)
        session.approval_status = approval_decision
        
        # Auto-approve if not required
        if approval_decision == ApprovalStatus.NOT_REQUIRED:
            session.checkout_status = CheckoutStatus.APPROVED
        
        # Store session
        storage.add_checkout_session(session)
        
        # Create audit event
        storage.create_audit_event(
            event_type="session_created",
            session_id=session_id,
            actor="checkout_api",
            details={
                "product_id": request.product_id,
                "quantity": request.quantity,
                "total": total
            }
        )
        
        # Determine risk factors for approval
        risk_factors = self._calculate_risk_factors(session, request.buyer_intent)
        requires_approval = approval_decision == ApprovalStatus.PENDING
        
        return CheckoutResponse(
            session=session,
            requires_approval=requires_approval,
            approval_risk_factors=risk_factors if requires_approval else None
        )
    
    def get_checkout_session(self, session_id: str) -> Optional[CheckoutSession]:
        """Get checkout session by ID."""
        return storage.get_checkout_session(session_id)
    
    def update_checkout_session(
        self,
        session_id: str,
        quantity: Optional[int] = None,
        shipping_method: Optional[str] = None
    ) -> Optional[CheckoutSession]:
        """Update checkout session quantity or shipping method."""
        session = storage.get_checkout_session(session_id)
        if not session:
            return None
        
        # Prevent updates if session is already completed
        if session.checkout_status in [CheckoutStatus.COMPLETED, CheckoutStatus.CANCELLED]:
            raise ValueError(f"Cannot update session in status: {session.checkout_status}")
        
        # Update quantity if provided
        if quantity is not None:
            product = catalog_manager.get_product_by_id(session.line_item.product_id)
            if not catalog_manager.check_availability(session.line_item.product_id, quantity):
                raise ValueError("Insufficient inventory for requested quantity")
            
            # Recalculate line item
            session.line_item.quantity = quantity
            session.line_item.total_price = product.price * quantity
        
        # Update shipping if provided
        if shipping_method and shipping_method in self.shipping_options:
            shipping_config = self.shipping_options[shipping_method]
            session.shipping_option = ShippingOption(**shipping_config)
        
        # Recalculate totals
        session.subtotal = session.line_item.total_price
        session.tax = session.subtotal * 0.08
        session.total = session.subtotal + session.tax + session.shipping_option.cost
        session.updated_at = datetime.now()
        
        # Update storage
        storage.update_checkout_session(session)
        
        # Create audit event
        storage.create_audit_event(
            event_type="product_selected",  # Using existing event type for updates
            session_id=session_id,
            actor="checkout_api",
            details={
                "new_quantity": session.line_item.quantity,
                "new_shipping": session.shipping_option.method,
                "new_total": session.total
            }
        )
        
        return session
    
    def approve_checkout_session(
        self,
        session_id: str,
        approved: bool,
        approver: Optional[str] = None,
        rationale: Optional[str] = None
    ) -> bool:
        """
        Approve or reject a checkout session.
        
        Args:
            session_id: The session ID
            approved: Whether the session is approved
            approver: Approver identifier
            rationale: Approval/rejection rationale
            
        Returns:
            bool: True if operation successful
        """
        print(f"DEBUG: Approving session {session_id}, approved={approved}")
        session = storage.get_checkout_session(session_id)
        if not session:
            print(f"DEBUG: Session {session_id} not found")
            return False
        
        print(f"DEBUG: Session found, current status: {session.approval_status}")
        
        # Update session status
        if approved:
            session.checkout_status = CheckoutStatus.APPROVED
            session.approval_status = ApprovalStatus.APPROVED
            event_type = "approval_granted"
        else:
            session.checkout_status = CheckoutStatus.REJECTED
            session.approval_status = ApprovalStatus.REJECTED
            event_type = "approval_rejected"
        
        session.updated_at = datetime.now()
        
        # Store approval decision
        from ..models.schemas import ApprovalDecision
        approval = ApprovalDecision(
            session_id=session_id,
            approver=approver,
            decision=session.approval_status,
            rationale=rationale,
            timestamp=datetime.now()
        )
        storage.add_approval(approval)
        
        # Update storage
        storage.update_checkout_session(session)
        
        # Create audit event
        storage.create_audit_event(
            event_type=event_type,
            session_id=session_id,
            actor=approver or "approval_system",
            details={
                "decision": session.approval_status,
                "rationale": rationale
            }
        )
        
        return True
    
    def complete_checkout_session(self, session_id: str) -> bool:
        """
        Complete a checkout session (initiate settlement).
        
        Args:
            session_id: The session ID to complete
            
        Returns:
            bool: True if completion initiated successfully
        """
        session = storage.get_checkout_session(session_id)
        if not session:
            return False
        
        # Verify session is approved
        if session.checkout_status != CheckoutStatus.APPROVED:
            raise ValueError(f"Session not approved: {session.checkout_status}")
        
        # Reserve inventory (mock)
        if not catalog_manager.reserve_inventory(session.line_item.product_id, session.line_item.quantity):
            raise ValueError("Failed to reserve inventory")
        
        # Update session status
        session.checkout_status = CheckoutStatus.COMPLETED
        session.updated_at = datetime.now()
        print(f"DEBUG: Updating session {session_id} status to COMPLETED")
        storage.update_checkout_session(session)
        
        # Create audit event
        storage.create_audit_event(
            event_type="session_completed",
            session_id=session_id,
            actor="checkout_api",
            details={
                "final_total": session.total,
                "completed_at": session.updated_at.isoformat()
            }
        )
        
        # Initiate settlement
        print(f"DEBUG: Initiating settlement for completed session {session_id}")
        from ..settlement.escrow import settlement_engine
        settlement = settlement_engine.initiate_settlement(session)
        print(f"DEBUG: Settlement created: {settlement.settlement_id if settlement else 'None'}")
        
        return True
    
    def _assess_approval_requirement(
        self,
        session: CheckoutSession,
        buyer_intent: Optional[object]
    ) -> ApprovalStatus:
        """Assess whether approval is required for a session."""
        # Simple approval logic for demo
        if session.total > 100.0:  # High value requires approval
            return ApprovalStatus.PENDING
        elif session.line_item.product_id.startswith("prod_003"):  # Specific product requires approval
            return ApprovalStatus.PENDING
        else:
            return ApprovalStatus.NOT_REQUIRED
    
    def _calculate_risk_factors(
        self,
        session: CheckoutSession,
        buyer_intent: Optional[object]
    ) -> List[str]:
        """Calculate risk factors for approval decision."""
        risk_factors = []
        
        if session.total > 100.0:
            risk_factors.append("high_value")
        
        if session.line_item.product_id.startswith("prod_003"):
            risk_factors.append("premium_product")
        
        if session.shipping_option.method == "overnight":
            risk_factors.append("expedited_shipping")
        
        return risk_factors


# Global checkout manager instance
checkout_manager = CheckoutManager()
