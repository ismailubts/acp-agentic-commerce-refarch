"""
Buyer agent with LangGraph workflow for autonomous shopping decisions.
"""

import re
from typing import Dict, List, Optional, TypedDict, Annotated
from datetime import datetime

from langgraph.graph import StateGraph, END

from ..models.schemas import (
    BuyerIntent,
    Product,
    CheckoutRequest,
    CheckoutResponse,
    AuditEventType
)
from ..merchant.catalog import catalog_manager
from ..merchant.checkout_api import checkout_manager
from ..storage import storage
from .approval_agent import approval_agent


class AgentState(TypedDict):
    """State for buyer agent workflow."""
    messages: List[str]
    user_request: str
    budget: Optional[float]
    parsed_intent: Optional[BuyerIntent]
    shortlisted_products: List[Product]
    selected_product: Optional[Product]
    checkout_session: Optional[CheckoutResponse]
    approval_required: bool
    approval_decision: Optional[str]
    workflow_complete: bool
    error_message: Optional[str]


class BuyerAgent:
    """Buyer agent with LangGraph workflow for autonomous shopping."""
    
    def __init__(self):
        """Initialize buyer agent with workflow graph."""
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("parse_intent", self._parse_intent)
        workflow.add_node("shortlist_products", self._shortlist_products)
        workflow.add_node("choose_product", self._choose_product)
        workflow.add_node("create_checkout_session", self._create_checkout_session)
        workflow.add_node("request_approval", self._request_approval)
        workflow.add_node("complete_checkout", self._complete_checkout)
        
        # Define flow
        workflow.set_entry_point("parse_intent")
        
        workflow.add_edge("parse_intent", "shortlist_products")
        workflow.add_edge("shortlist_products", "choose_product")
        workflow.add_edge("choose_product", "create_checkout_session")
        workflow.add_conditional_edges(
            "create_checkout_session",
            self._should_request_approval,
            {
                "approval": "request_approval",
                "complete": "complete_checkout"
            }
        )
        workflow.add_conditional_edges(
            "request_approval",
            self._check_approval_decision,
            {
                "approved": "complete_checkout",
                "rejected": END,
                "pending": "request_approval"
            }
        )
        workflow.add_edge("complete_checkout", END)
        
        return workflow.compile()
    
    def _parse_intent(self, state: AgentState) -> AgentState:
        """Parse user request to extract shopping intent."""
        try:
            user_request = state["user_request"]
            
            # Simple intent parsing - extract budget and category
            budget = self._extract_budget(user_request)
            category = self._extract_category(user_request)
            max_shipping_days = self._extract_shipping_preference(user_request)
            
            parsed_intent = BuyerIntent(
                max_price=budget,
                category=category,
                max_shipping_days=max_shipping_days,
                special_requirements=user_request
            )
            
            # Create audit event
            storage.create_audit_event(
                event_type=AuditEventType.SESSION_CREATED,
                actor="buyer_agent",
                details={
                    "user_request": user_request,
                    "parsed_intent": parsed_intent.dict()
                }
            )
            
            return {
                **state,
                "budget": budget,
                "parsed_intent": parsed_intent,
                "messages": [f"Intent parsed: budget=${budget}, category={category}"]
            }
            
        except Exception as e:
            return {
                **state,
                "error_message": f"Failed to parse intent: {str(e)}",
                "workflow_complete": True
            }
    
    def _shortlist_products(self, state: AgentState) -> AgentState:
        """Shortlist products based on parsed intent."""
        try:
            intent = state["parsed_intent"]
            
            if not intent.category or not intent.max_price:
                return {
                    **state,
                    "error_message": "Missing category or budget in intent",
                    "workflow_complete": True
                }
            
            # Get shortlisted candidates
            candidates = catalog_manager.get_shortlisted_candidates(
                category=intent.category,
                max_price=intent.max_price,
                max_shipping_days=intent.max_shipping_days or 7,
                limit=5
            )
            
            # Create audit event
            storage.create_audit_event(
                event_type=AuditEventType.PRODUCTS_SHORTLISTED,
                actor="buyer_agent",
                details={
                    "category": intent.category,
                    "max_price": intent.max_price,
                    "candidates_found": len(candidates)
                }
            )
            
            return {
                **state,
                "shortlisted_products": candidates,
                "messages": [f"Found {len(candidates)} candidates"]
            }
            
        except Exception as e:
            return {
                **state,
                "error_message": f"Failed to shortlist products: {str(e)}",
                "workflow_complete": True
            }
    
    def _choose_product(self, state: AgentState) -> AgentState:
        """Choose best product from shortlisted candidates."""
        try:
            candidates = state["shortlisted_products"]
            budget = state["budget"]
            
            if not candidates:
                return {
                    **state,
                    "error_message": "No products found matching criteria",
                    "workflow_complete": True
                }
            
            # Simple selection: choose best value (price vs features)
            selected = self._select_best_product(candidates, budget)
            
            # Create audit event
            storage.create_audit_event(
                event_type=AuditEventType.PRODUCT_SELECTED,
                actor="buyer_agent",
                details={
                    "selected_product": selected.dict(),
                    "total_candidates": len(candidates)
                }
            )
            
            return {
                **state,
                "selected_product": selected,
                "messages": [f"Selected: {selected.name} - ${selected.price}"]
            }
            
        except Exception as e:
            return {
                **state,
                "error_message": f"Failed to choose product: {str(e)}",
                "workflow_complete": True
            }
    
    def _create_checkout_session(self, state: AgentState) -> AgentState:
        """Create checkout session for selected product."""
        try:
            product = state["selected_product"]
            intent = state["parsed_intent"]
            
            checkout_request = CheckoutRequest(
                product_id=product.id,
                quantity=1,
                buyer_intent=intent
            )
            
            checkout_response = checkout_manager.create_checkout_session(checkout_request)
            
            # Create audit event
            storage.create_audit_event(
                event_type=AuditEventType.CHECKOUT_SESSION_CREATED,
                actor="buyer_agent",
                details={
                    "session_id": checkout_response.session.session_id,
                    "product_id": product.id,
                    "total": checkout_response.session.total
                }
            )
            
            return {
                **state,
                "checkout_session": checkout_response,
                "messages": [("assistant", f"Checkout created: {checkout_response.session.session_id}")]
            }
            
        except Exception as e:
            return {
                **state,
                "error_message": f"Failed to create checkout session: {str(e)}",
                "workflow_complete": True
            }
    
    def _request_approval(self, state: AgentState) -> AgentState:
        """Request human approval for checkout session."""
        try:
            session = state["checkout_session"].session
            product = state["selected_product"]
            
            # Submit approval request
            approval_id = approval_agent.request_approval(
                session_id=session.session_id,
                product_name=product.name,
                total_amount=session.total,
                risk_factors=session.approval_risk_factors or []
            )
            
            # Create audit event
            storage.create_audit_event(
                event_type=AuditEventType.APPROVAL_REQUESTED,
                actor="buyer_agent",
                details={
                    "session_id": session.session_id,
                    "approval_id": approval_id,
                    "risk_factors": session.approval_risk_factors
                }
            )
            
            return {
                **state,
                "messages": [f"Approval requested: {approval_id}"]
            }
            
        except Exception as e:
            return {
                **state,
                "error_message": f"Failed to request approval: {str(e)}",
                "workflow_complete": True
            }
    
    def _complete_checkout(self, state: AgentState) -> AgentState:
        """Complete checkout process."""
        try:
            session = state["checkout_session"].session
            
            # Check if session is approved before completing
            if session.checkout_status != "approved":
                return {
                    **state,
                    "error_message": f"Cannot complete checkout: session status is {session.checkout_status}",
                    "workflow_complete": True
                }
            
            # Complete checkout session
            success = checkout_manager.complete_checkout_session(session.session_id)
            
            if success:
                # Create audit event
                storage.create_audit_event(
                    event_type=AuditEventType.SESSION_COMPLETED,
                    actor="buyer_agent",
                    details={
                        "session_id": session.session_id,
                        "final_total": session.total
                    }
                )
                
                return {
                    **state,
                    "workflow_complete": True,
                    "messages": [f"Checkout completed: {session.session_id}"]
                }
            else:
                return {
                    **state,
                    "error_message": "Failed to complete checkout",
                    "workflow_complete": True
                }
                
        except Exception as e:
            return {
                **state,
                "error_message": f"Failed to complete checkout: {str(e)}",
                "workflow_complete": True
            }
    
    def _should_request_approval(self, state: AgentState) -> str:
        """Determine if approval is required."""
        return "approval" if state.get("approval_required", False) else "complete"
    
    def _check_approval_decision(self, state: AgentState) -> str:
        """Check approval decision status."""
        session_id = state["checkout_session"].session.session_id
        
        # Get approval status
        approval_status = approval_agent.get_approval_status(session_id)
        
        if approval_status == "approved":
            return "approved"
        elif approval_status == "rejected":
            return "rejected"
        else:
            return "pending"
    
    def _extract_budget(self, text: str) -> Optional[float]:
        """Extract budget from text."""
        # Look for dollar amounts
        patterns = [
            r'\$(\d+\.?\d*)',
            r'(\d+)\s*dollars?',
            r'budget.*?(\d+\.?\d*)',
            r'under\s+(\d+\.?\d*)',
            r'less\s+than\s+(\d+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def _extract_category(self, text: str) -> Optional[str]:
        """Extract product category from text."""
        text_lower = text.lower()
        
        # Simple keyword matching
        if any(keyword in text_lower for keyword in ['laptop bag', 'laptop sleeve', 'briefcase']):
            return 'laptop_bag'
        elif any(keyword in text_lower for keyword in ['backpack', 'rucksack']):
            return 'backpack'
        elif any(keyword in text_lower for keyword in ['accessory', 'organizer', 'cable']):
            return 'accessory'
        
        return None
    
    def _extract_shipping_preference(self, text: str) -> Optional[int]:
        """Extract shipping preference from text."""
        text_lower = text.lower()
        
        if 'overnight' in text_lower or '1 day' in text_lower:
            return 1
        elif 'express' in text_lower or 'fast' in text_lower or '2-3 days' in text_lower:
            return 3
        elif 'standard' in text_lower or 'regular' in text_lower:
            return 7
        
        return None
    
    def _select_best_product(self, candidates: List[Product], budget: float) -> Product:
        """Select best product from candidates."""
        # Simple scoring: value for money
        best_product = None
        best_score = -1
        
        for product in candidates:
            # Score based on price efficiency and shipping speed
            price_score = (budget - product.price) / budget  # Lower price = higher score
            shipping_score = (7 - product.shipping_eta_days) / 7  # Faster shipping = higher score
            total_score = price_score * 0.7 + shipping_score * 0.3
            
            if total_score > best_score:
                best_score = total_score
                best_product = product
        
        return best_product
    
    def process_request(self, user_request: str) -> Dict:
        """Process a shopping request through the workflow."""
        initial_state = AgentState(
            messages=[],
            user_request=user_request,
            budget=None,
            parsed_intent=None,
            shortlisted_products=[],
            selected_product=None,
            checkout_session=None,
            approval_required=False,
            approval_decision=None,
            workflow_complete=False,
            error_message=None
        )
        
        # Run workflow
        result = self.workflow.invoke(initial_state)
        
        return {
            "success": not result.get("error_message"),
            "error_message": result.get("error_message"),
            "selected_product": result.get("selected_product"),
            "checkout_session": result.get("checkout_session"),
            "approval_required": result.get("approval_required", False),
            "workflow_complete": result.get("workflow_complete", False),
            "messages": result.get("messages", [])
        }


# Global buyer agent instance
buyer_agent = BuyerAgent()
