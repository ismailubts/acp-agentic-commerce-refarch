"""
Approval agent for managing human-in-the-loop approval boundary.
"""

from datetime import datetime
from typing import Dict, List, Optional
import uuid

from ..models.schemas import ApprovalStatus, AuditEventType
from ..merchant.checkout_api import checkout_manager
from ..storage import storage


class ApprovalRequest:
    """Represents an approval request."""
    
    def __init__(
        self,
        approval_id: str,
        session_id: str,
        product_name: str,
        total_amount: float,
        risk_factors: List[str],
        created_at: datetime,
        status: str = "pending"
    ):
        self.approval_id = approval_id
        self.session_id = session_id
        self.product_name = product_name
        self.total_amount = total_amount
        self.risk_factors = risk_factors
        self.created_at = created_at
        self.status = status
        self.decision_time: Optional[datetime] = None
        self.decision_maker: Optional[str] = None
        self.rationale: Optional[str] = None


class ApprovalAgent:
    """Manages human approval boundary with clear state tracking."""
    
    def __init__(self):
        """Initialize approval agent."""
        self.approval_requests: Dict[str, ApprovalRequest] = {}
        self._approval_counter = 2000
    
    def _generate_approval_id(self) -> str:
        """Generate a unique approval ID."""
        self._approval_counter += 1
        return f"approval_{self._approval_counter}"
    
    def request_approval(
        self,
        session_id: str,
        product_name: str,
        total_amount: float,
        risk_factors: List[str]
    ) -> str:
        """
        Request human approval for a checkout session.
        
        Args:
            session_id: Checkout session ID
            product_name: Name of the selected product
            total_amount: Total transaction amount
            risk_factors: List of identified risk factors
            
        Returns:
            str: Approval request ID
        """
        approval_id = self._generate_approval_id()
        
        approval_request = ApprovalRequest(
            approval_id=approval_id,
            session_id=session_id,
            product_name=product_name,
            total_amount=total_amount,
            risk_factors=risk_factors,
            created_at=datetime.now()
        )
        
        self.approval_requests[approval_id] = approval_request
        
        # Create audit event
        storage.create_audit_event(
            event_type=AuditEventType.APPROVAL_REQUESTED,
            session_id=session_id,
            actor="approval_agent",
            details={
                "approval_id": approval_id,
                "product_name": product_name,
                "total_amount": total_amount,
                "risk_factors": risk_factors
            }
        )
        
        return approval_id
    
    def approve_request(
        self,
        approval_id: str,
        approver: str,
        rationale: Optional[str] = None
    ) -> bool:
        """
        Approve an approval request.
        
        Args:
            approval_id: Approval request ID
            approver: Person or system making the approval
            rationale: Optional approval rationale
            
        Returns:
            bool: True if approval successful
        """
        if approval_id not in self.approval_requests:
            return False
        
        request = self.approval_requests[approval_id]
        
        if request.status != "pending":
            return False
        
        # Update request
        request.status = "approved"
        request.decision_time = datetime.now()
        request.decision_maker = approver
        request.rationale = rationale
        
        # Update checkout session
        success = checkout_manager.approve_checkout_session(
            session_id=request.session_id,
            approved=True,
            approver=approver,
            rationale=rationale
        )
        
        if success:
            # Create audit event
            storage.create_audit_event(
                event_type=AuditEventType.APPROVAL_GRANTED,
                session_id=request.session_id,
                actor="approval_agent",
                details={
                    "approval_id": approval_id,
                    "approver": approver,
                    "rationale": rationale
                }
            )
        
        return success
    
    def reject_request(
        self,
        approval_id: str,
        approver: str,
        rationale: Optional[str] = None
    ) -> bool:
        """
        Reject an approval request.
        
        Args:
            approval_id: Approval request ID
            approver: Person or system making the rejection
            rationale: Optional rejection rationale
            
        Returns:
            bool: True if rejection successful
        """
        if approval_id not in self.approval_requests:
            return False
        
        request = self.approval_requests[approval_id]
        
        if request.status != "pending":
            return False
        
        # Update request
        request.status = "rejected"
        request.decision_time = datetime.now()
        request.decision_maker = approver
        request.rationale = rationale
        
        # Update checkout session
        success = checkout_manager.approve_checkout_session(
            session_id=request.session_id,
            approved=False,
            approver=approver,
            rationale=rationale
        )
        
        if success:
            # Create audit event
            storage.create_audit_event(
                event_type=AuditEventType.APPROVAL_REJECTED,
                session_id=request.session_id,
                actor="approval_agent",
                details={
                    "approval_id": approval_id,
                    "approver": approver,
                    "rationale": rationale
                }
            )
        
        return success
    
    def get_approval_status(self, session_id: str) -> Optional[str]:
        """
        Get approval status for a session.
        
        Args:
            session_id: Checkout session ID
            
        Returns:
            Optional[str]: Approval status or None if not found
        """
        # Find approval request for this session
        for request in self.approval_requests.values():
            if request.session_id == session_id:
                return request.status
        
        return None
    
    def get_approval_request(self, approval_id: str) -> Optional[ApprovalRequest]:
        """
        Get approval request by ID.
        
        Args:
            approval_id: Approval request ID
            
        Returns:
            Optional[ApprovalRequest]: Approval request or None if not found
        """
        return self.approval_requests.get(approval_id)
    
    def get_pending_approvals(self) -> List[ApprovalRequest]:
        """
        Get all pending approval requests.
        
        Returns:
            List[ApprovalRequest]: List of pending requests
        """
        return [
            request for request in self.approval_requests.values()
            if request.status == "pending"
        ]
    
    def get_approval_history(self, session_id: str) -> List[ApprovalRequest]:
        """
        Get approval history for a session.
        
        Args:
            session_id: Checkout session ID
            
        Returns:
            List[ApprovalRequest]: List of approval requests for the session
        """
        return [
            request for request in self.approval_requests.values()
            if request.session_id == session_id
        ]
    
    def get_approval_summary(self) -> Dict:
        """
        Get summary of approval statistics.
        
        Returns:
            Dict: Approval statistics
        """
        total_requests = len(self.approval_requests)
        pending_count = len(self.get_pending_approvals())
        approved_count = len([r for r in self.approval_requests.values() if r.status == "approved"])
        rejected_count = len([r for r in self.approval_requests.values() if r.status == "rejected"])
        
        return {
            "total_requests": total_requests,
            "pending": pending_count,
            "approved": approved_count,
            "rejected": rejected_count,
            "approval_rate": approved_count / total_requests if total_requests > 0 else 0
        }
    
    def clear_old_requests(self, hours: int = 24) -> int:
        """
        Clear old approval requests.
        
        Args:
            hours: Age in hours to clear requests
            
        Returns:
            int: Number of requests cleared
        """
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        old_request_ids = [
            approval_id for approval_id, request in self.approval_requests.items()
            if request.created_at.timestamp() < cutoff_time and request.status != "pending"
        ]
        
        for approval_id in old_request_ids:
            del self.approval_requests[approval_id]
        
        return len(old_request_ids)


# Global approval agent instance
approval_agent = ApprovalAgent()
