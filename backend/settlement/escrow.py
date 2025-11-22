"""
Mock settlement and escrow services for the BoundCart governed agent commerce reference.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from ..models.schemas import SettlementEvent, CheckoutSession, CheckoutStatus
from ..storage import storage


class MockEscrowService:
    """Mock escrow service for simulating payment settlement."""
    
    def __init__(self):
        """Initialize mock escrow service."""
        self.provider_name = "mock_escrow"
    
    def create_settlement(
        self,
        session_id: str,
        amount: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SettlementEvent:
        """
        Create a settlement record for an approved checkout session.
        
        Args:
            session_id: The checkout session ID
            amount: The settlement amount
            
        Returns:
            SettlementEvent: The created settlement record
        """
        settlement_id = storage.generate_settlement_id()
        
        settlement = SettlementEvent(
            settlement_id=settlement_id,
            session_id=session_id,
            amount=amount,
            provider=self.provider_name,
            status="created",
            created_at=datetime.now()
        )
        
        storage.add_settlement(settlement)
        
        # Create audit event
        storage.create_audit_event(
            event_type="settlement_created",
            session_id=session_id,
            actor="settlement_system",
            details={
                "settlement_id": settlement_id,
                "amount": amount,
                "provider": self.provider_name
            }
        )
        
        return settlement
    
    def process_settlement(self, settlement_id: str) -> bool:
        """
        Process a settlement (mock payment processing).
        
        Args:
            settlement_id: The settlement ID to process
            
        Returns:
            bool: True if processing successful
        """
        settlement = storage.get_settlement(settlement_id)
        if not settlement:
            return False
        
        # Mock payment processing - always succeeds in this demo
        settlement.status = "completed"
        settlement.completed_at = datetime.now()
        
        # Update the settlement in storage
        storage.add_settlement(settlement)
        
        # Create audit event
        storage.create_audit_event(
            event_type="settlement_completed",
            session_id=settlement.session_id,
            actor="settlement_system",
            details={
                "settlement_id": settlement_id,
                "amount": settlement.amount,
                "completed_at": settlement.completed_at.isoformat()
            }
        )
        
        return True
    
    def get_settlement_status(self, settlement_id: str) -> Optional[str]:
        """Get settlement status by ID."""
        settlement = storage.get_settlement(settlement_id)
        return settlement.status if settlement else None
    
    def get_settlement_by_session(self, session_id: str) -> Optional[SettlementEvent]:
        """Get settlement event by session ID."""
        return storage.get_settlement_by_session(session_id)
    
    def validate_payment_method(self, payment_method: Dict[str, Any]) -> bool:
        """
        Mock payment method validation.
        
        Args:
            payment_method: Payment method details
            
        Returns:
            bool: True if payment method is valid
        """
        # Mock validation - check for required fields
        required_fields = ["type", "identifier"]
        return all(field in payment_method for field in required_fields)
    
    def calculate_fees(self, amount: float) -> float:
        """
        Calculate mock processing fees.
        
        Args:
            amount: Transaction amount
            
        Returns:
            float: Processing fee amount
        """
        # Mock fee calculation: 2.9% + $0.30
        return (amount * 0.029) + 0.30


class SettlementEngine:
    """Coordinates settlement operations for checkout sessions."""
    
    def __init__(self):
        """Initialize settlement engine."""
        self.escrow_service = MockEscrowService()
    
    def initiate_settlement(
        self,
        session: CheckoutSession,
        payment_method: Optional[Dict[str, Any]] = None
    ) -> Optional[SettlementEvent]:
        """
        Initiate settlement for an approved checkout session.
        
        Args:
            session: The checkout session
            payment_method: Payment method details
            
        Returns:
            SettlementEvent: The created settlement record
        """
        print(f"DEBUG: Initiating settlement for session {session.session_id}")
        print(f"DEBUG: Session status: {session.checkout_status}")
        
        # Validate session is approved and completed
        if session.checkout_status != CheckoutStatus.COMPLETED:
            print(f"DEBUG: Session not completed, status: {session.checkout_status}")
            return None
        
        # Validate payment method (mock)
        if payment_method and not self.escrow_service.validate_payment_method(payment_method):
            return None
        
        # Create settlement record
        settlement = self.escrow_service.create_settlement(
            session_id=session.session_id,
            amount=session.total,
            metadata={
                "checkout_status": session.checkout_status,
                "approval_status": session.approval_status,
                "payment_method": payment_method
            }
        )
        
        # Process settlement immediately in this mock implementation
        self.escrow_service.process_settlement(settlement.settlement_id)
        
        return settlement
    
    def complete_settlement(self, session_id: str) -> bool:
        """
        Complete settlement for a session.
        
        Args:
            session_id: The checkout session ID
            
        Returns:
            bool: True if settlement completed successfully
        """
        settlement = self.escrow_service.get_settlement_by_session(session_id)
        if not settlement:
            return False
        
        return self.escrow_service.process_settlement(settlement.settlement_id)
    
    def get_settlement_by_session(self, session_id: str) -> Optional[SettlementEvent]:
        """Get settlement event by session ID."""
        return self.escrow_service.get_settlement_by_session(session_id)
    
    def get_settlement_status(self, session_id: str) -> Optional[str]:
        """Get settlement status for a session."""
        settlement = self.escrow_service.get_settlement_by_session(session_id)
        return settlement.status if settlement else None


# Global settlement engine instance
settlement_engine = SettlementEngine()
