"""
FastAPI application for the ACP Agentic Commerce Reference governed agent commerce reference.
"""

import sys
import os
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

# Add project root to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from backend.models.schemas import (
    Product,
    CheckoutRequest,
    CheckoutResponse,
    ApprovalRequest,
    SessionUpdateRequest,
    CheckoutSession,
    SettlementEvent,
    AuditEvent
)
from backend.merchant.catalog import catalog_manager
from backend.merchant.checkout_api import checkout_manager
from backend.settlement.escrow import settlement_engine
from backend.storage import storage

from pydantic import BaseModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Initialize catalog on startup
    try:
        catalog_manager._load_catalog()
        print(f"Catalog loaded with {len(catalog_manager.get_all_products())} products")
    except Exception as e:
        print(f"Failed to load catalog: {e}")
    
    yield
    
    # Cleanup on shutdown
    print("Application shutting down")


# Create FastAPI app
app = FastAPI(
    title="ACP Agentic Commerce Reference — Governed Agent Commerce",
    description="Reference implementation for governed delegation across commerce trust boundaries",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "products_loaded": len(catalog_manager.get_all_products())
    }


# Product endpoints
@app.get("/products", response_model=List[Product])
async def get_products(
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    max_shipping_days: Optional[int] = None
):
    """Get products with optional filtering."""
    if category or max_price is not None or max_shipping_days is not None:
        products = catalog_manager.search_candidates(
            category=category,
            max_price=max_price,
            max_shipping_days=max_shipping_days
        )
    else:
        products = catalog_manager.get_all_products()
    
    return products


@app.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """Get a specific product by ID."""
    product = catalog_manager.get_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product not found: {product_id}"
        )
    return product


# Checkout endpoints
@app.post("/checkout/session", response_model=CheckoutResponse)
async def create_checkout_session(request: CheckoutRequest):
    """Create a new checkout session."""
    try:
        response = checkout_manager.create_checkout_session(request)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session: {e}"
        )


@app.get("/checkout/session/{session_id}", response_model=CheckoutSession)
async def get_checkout_session(session_id: str):
    """Get a checkout session by ID."""
    session = checkout_manager.get_checkout_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkout session not found: {session_id}"
        )
    return session


@app.patch("/checkout/session/{session_id}", response_model=CheckoutSession)
async def update_checkout_session(session_id: str, request: SessionUpdateRequest):
    """Update a checkout session."""
    try:
        session = checkout_manager.update_checkout_session(
            session_id=session_id,
            quantity=request.quantity,
            shipping_method=request.shipping_method
        )
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Checkout session not found: {session_id}"
            )
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update checkout session: {e}"
        )


@app.post("/checkout/session/{session_id}/approve")
async def approve_checkout_session(session_id: str, request: ApprovalRequest):
    """Approve or reject a checkout session."""
    try:
        approved = request.decision == "approved"
        success = checkout_manager.approve_checkout_session(
            session_id=session_id,
            approved=approved,
            approver=request.approver,
            rationale=request.rationale
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Checkout session not found: {session_id}"
            )
        
        return {"message": f"Session {session_id} {request.decision}"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process approval: {e}"
        )


@app.post("/checkout/session/{session_id}/complete")
async def complete_checkout_session(session_id: str):
    """Complete a checkout session (initiate settlement)."""
    try:
        # Complete the checkout session
        success = checkout_manager.complete_checkout_session(session_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Checkout session not found: {session_id}"
            )
        
        # Initiate settlement
        session = checkout_manager.get_checkout_session(session_id)
        settlement = settlement_engine.initiate_settlement(session)
        
        if not settlement:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initiate settlement"
            )
        
        return {
            "message": f"Session {session_id} completed",
            "settlement_id": settlement.settlement_id
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete checkout session: {e}"
        )


# Audit endpoints
@app.get("/audit/{session_id}", response_model=List[AuditEvent])
async def get_audit_events(session_id: str):
    """Get audit events for a specific session."""
    events = storage.get_audit_events(session_id)
    return events


@app.get("/audit", response_model=List[AuditEvent])
async def get_all_audit_events():
    """Get all audit events."""
    events = storage.get_audit_events()
    return events


# Settlement endpoints
@app.get("/settlement/{session_id}", response_model=Optional[SettlementEvent])
async def get_settlement(session_id: str):
    """Get settlement information for a session."""
    settlement = settlement_engine.escrow_service.get_settlement_by_session(session_id)
    return settlement


@app.get("/settlement/{settlement_id}/status")
async def get_settlement_status(settlement_id: str):
    """Get settlement status by settlement ID."""
    status = settlement_engine.escrow_service.get_settlement_status(settlement_id)
    if status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Settlement not found: {settlement_id}"
        )
    return {"settlement_id": settlement_id, "status": status}


# Agent request/response models
class ShoppingRequest(BaseModel):
    """Request for buyer agent shopping workflow."""
    user_request: str

class ShoppingResponse(BaseModel):
    """Response from buyer agent shopping workflow."""
    success: bool
    error_message: Optional[str] = None
    selected_product: Optional[Product] = None
    checkout_session: Optional[CheckoutResponse] = None
    approval_required: bool = False
    workflow_complete: bool = False
    messages: List[str] = []

class ApprovalActionRequest(BaseModel):
    """Request for approval action."""
    approval_id: str
    approver: str
    rationale: Optional[str] = None

class ApprovalStatusResponse(BaseModel):
    """Response for approval status."""
    approval_id: str
    status: str
    session_id: str
    product_name: str
    total_amount: float
    risk_factors: List[str]
    created_at: datetime
    decision_time: Optional[datetime] = None
    decision_maker: Optional[str] = None
    rationale: Optional[str] = None


# Agent endpoints
@app.post("/agent/shop", response_model=ShoppingResponse)
async def shop_with_agent(request: ShoppingRequest):
    """Process shopping request with buyer agent."""
    try:
        from .agents.buyer_agent import buyer_agent
        
        result = buyer_agent.process_request(request.user_request)
        
        return ShoppingResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent processing failed: {e}"
        )


@app.get("/agent/approvals/pending")
async def get_pending_approvals():
    """Get all pending approval requests."""
    try:
        from .agents.approval_agent import approval_agent
        
        pending_requests = approval_agent.get_pending_approvals()
        
        return [
            ApprovalStatusResponse(
                approval_id=request.approval_id,
                status=request.status,
                session_id=request.session_id,
                product_name=request.product_name,
                total_amount=request.total_amount,
                risk_factors=request.risk_factors,
                created_at=request.created_at,
                decision_time=request.decision_time,
                decision_maker=request.decision_maker,
                rationale=request.rationale
            )
            for request in pending_requests
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending approvals: {e}"
        )


@app.post("/agent/approvals/{approval_id}/approve")
async def approve_request(approval_id: str, request: ApprovalActionRequest):
    """Approve an approval request."""
    try:
        from .agents.approval_agent import approval_agent
        
        success = approval_agent.approve_request(
            approval_id=approval_id,
            approver=request.approver,
            rationale=request.rationale
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval request not found or already processed: {approval_id}"
            )
        
        return {"message": f"Approval request {approval_id} approved"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve request: {e}"
        )


@app.post("/agent/approvals/{approval_id}/reject")
async def reject_request(approval_id: str, request: ApprovalActionRequest):
    """Reject an approval request."""
    try:
        from .agents.approval_agent import approval_agent
        
        success = approval_agent.reject_request(
            approval_id=approval_id,
            approver=request.approver,
            rationale=request.rationale
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval request not found or already processed: {approval_id}"
            )
        
        return {"message": f"Approval request {approval_id} rejected"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject request: {e}"
        )


@app.get("/agent/approvals/{approval_id}")
async def get_approval_request(approval_id: str):
    """Get specific approval request details."""
    try:
        from .agents.approval_agent import approval_agent
        
        request = approval_agent.get_approval_request(approval_id)
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval request not found: {approval_id}"
            )
        
        return ApprovalStatusResponse(
            approval_id=request.approval_id,
            status=request.status,
            session_id=request.session_id,
            product_name=request.product_name,
            total_amount=request.total_amount,
            risk_factors=request.risk_factors,
            created_at=request.created_at,
            decision_time=request.decision_time,
            decision_maker=request.decision_maker,
            rationale=request.rationale
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get approval request: {e}"
        )


@app.get("/agent/approvals/summary")
async def get_approval_summary():
    """Get approval statistics summary."""
    try:
        from .agents.approval_agent import approval_agent
        
        summary = approval_agent.get_approval_summary()
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get approval summary: {e}"
        )


# Utility endpoints
@app.get("/catalog/candidates")
async def get_shortlisted_candidates(
    category: str,
    max_price: float,
    max_shipping_days: int,
    limit: int = 5
):
    """Get shortlisted product candidates."""
    candidates = catalog_manager.get_shortlisted_candidates(
        category=category,
        max_price=max_price,
        max_shipping_days=max_shipping_days,
        limit=limit
    )
    return candidates


@app.get("/system/status")
async def get_system_status():
    """Get system status and statistics."""
    products = catalog_manager.get_all_products()
    sessions = storage.checkout_sessions
    settlements = storage.settlements
    audit_events = storage.audit_events
    
    return {
        "timestamp": datetime.now().isoformat(),
        "products": {
            "total": len(products),
            "categories": list(set(p.category for p in products)),
            "avg_price": sum(p.price for p in products) / len(products) if products else 0
        },
        "checkout_sessions": {
            "total": len(sessions),
            "by_status": {
                status.value: sum(1 for s in sessions.values() if s.checkout_status == status)
                for status in sessions.values() if hasattr(s.checkout_status, 'value')
            }
        },
        "settlements": {
            "total": len(settlements),
            "by_status": {
                status: sum(1 for s in settlements.values() if s.status == status)
                for status in set(s.status for s in settlements.values())
            }
        },
        "audit_events": {
            "total": len(audit_events),
            "by_type": {
                event_type.value: sum(1 for e in audit_events if e.event_type == event_type)
                for event_type in set(e.event_type for e in audit_events)
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
