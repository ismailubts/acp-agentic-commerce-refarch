"""
Simple HTTP server for the BoundCart governed agent commerce reference.
"""

import sys
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add project root to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.models.schemas import (
    Product,
    CheckoutRequest,
    CheckoutResponse,
    ApprovalRequest,
    SessionUpdateRequest,
    CheckoutSession,
    SettlementEvent,
    AuditEvent,
    BuyerIntent,
    LineItem,
    ShippingOption
)
from backend.merchant.catalog import catalog_manager
from backend.merchant.checkout_api import checkout_manager
from backend.settlement.escrow import settlement_engine
from backend.storage import storage


class CommerceHandler(BaseHTTPRequestHandler):
    """HTTP request handler for commerce API."""
    
    def _send_json_response(self, data: Dict[str, Any], status_code: int = 200):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def _send_error(self, message: str, status_code: int = 500):
        """Send error response."""
        self._send_json_response({"error": message}, status_code)
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS."""
        self._send_json_response({}, 200)
    
    def do_GET(self):
        """Handle GET requests."""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            print(f"DEBUG: GET path = '{path}'")  # Debug logging
            
            if path == '/health':
                products = catalog_manager.get_all_products()
                self._send_json_response({
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "products_loaded": len(products)
                })
            
            elif path == '/products':
                products = catalog_manager.get_all_products()
                products_data = []
                for p in products:
                    products_data.append({
                        "id": p.id,
                        "name": p.name,
                        "category": p.category,
                        "price": p.price,
                        "shipping_eta_days": p.shipping_eta_days,
                        "inventory": p.inventory,
                        "short_description": p.short_description
                    })
                self._send_json_response(products_data)
            
            elif path.startswith('/checkout/session/'):
                session_id = path.split('/')[-1]
                session = storage.get_checkout_session(session_id)
                if not session:
                    self._send_error("Session not found", 404)
                    return
                
                session_data = {
                    "session_id": session.session_id,
                    "line_item": {
                        "product_id": session.line_item.product_id,
                        "product_name": session.line_item.product_name,
                        "quantity": session.line_item.quantity,
                        "unit_price": session.line_item.unit_price,
                        "total_price": session.line_item.total_price
                    },
                    "shipping_option": {
                        "method": session.shipping_option.method,
                        "eta_days": session.shipping_option.eta_days,
                        "cost": session.shipping_option.cost
                    },
                    "subtotal": session.subtotal,
                    "tax": session.tax,
                    "total": session.total,
                    "checkout_status": session.checkout_status,
                    "approval_status": session.approval_status,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "approval_risk_factors": session.approval_risk_factors
                }
                self._send_json_response(session_data)
            
            elif path.startswith('/settlement/'):
                session_id = path.split('/')[-1]
                settlement = settlement_engine.get_settlement_by_session(session_id)
                if not settlement:
                    self._send_error("Settlement not found", 404)
                    return
                
                settlement_data = {
                    "settlement_id": settlement.settlement_id,
                    "session_id": settlement.session_id,
                    "amount": settlement.amount,
                    "status": settlement.status,
                    "provider": settlement.provider,
                    "created_at": settlement.created_at.isoformat(),
                    "completed_at": settlement.completed_at.isoformat() if settlement.completed_at else None,
                    "transaction_id": settlement.transaction_id
                }
                self._send_json_response(settlement_data)
            
            elif path.startswith('/audit/'):
                session_id = path.split('/')[-1]
                events = storage.get_audit_events_for_session(session_id)
                events_data = []
                for event in events:
                    events_data.append({
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "actor": event.actor,
                        "timestamp": event.timestamp.isoformat(),
                        "session_id": event.session_id,
                        "approval_id": event.approval_id,
                        "details": event.details
                    })
                self._send_json_response(events_data)
            
            elif path == '/agent/approvals/pending':
                # Get pending approvals
                pending_approvals = storage.get_pending_approvals()
                approvals_data = []
                for approval in pending_approvals:
                    approvals_data.append({
                        "approval_id": approval["approval_id"],
                        "session_id": approval["session_id"],
                        "status": approval["status"],
                        "total_amount": approval["total_amount"],
                        "product_name": approval["product_name"],
                        "risk_factors": approval["risk_factors"],
                        "created_at": approval["created_at"].isoformat() if hasattr(approval["created_at"], 'isoformat') else approval["created_at"],
                        "expires_at": approval["expires_at"].isoformat() if approval["expires_at"] and hasattr(approval["expires_at"], 'isoformat') else None
                    })
                self._send_json_response(approvals_data)
            
            elif path == '/agent/approvals/summary':
                # Get approval summary statistics
                pending_approvals = storage.get_pending_approvals()
                total_sessions = len(storage.checkout_sessions)
                pending_count = len(pending_approvals)
                
                # Count approved sessions
                approved_count = sum(1 for session in storage.checkout_sessions.values() 
                                   if session.approval_status == "approved")
                
                # Count rejected sessions  
                rejected_count = sum(1 for session in storage.checkout_sessions.values()
                                   if session.approval_status == "rejected")
                
                summary_data = {
                    "total_requests": total_sessions,
                    "pending": pending_count,
                    "approved": approved_count,
                    "rejected": rejected_count
                }
                self._send_json_response(summary_data)
            
            else:
                self._send_error("Not found", 404)
                
        except Exception as e:
            self._send_error(str(e))
    
    def do_POST(self):
        """Handle POST requests."""
        try:
            # Handle empty request body
            content_length = 0
            if 'Content-Length' in self.headers:
                content_length = int(self.headers['Content-Length'])
            
            data = {}
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
            
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            print(f"DEBUG: POST path = '{path}'")  # Debug logging
            
            if path == '/checkout/session':
                # Create buyer intent
                buyer_intent_data = data.get('buyer_intent', {})
                buyer_intent = BuyerIntent(
                    max_price=buyer_intent_data.get('max_price'),
                    category=buyer_intent_data.get('category'),
                    max_shipping_days=buyer_intent_data.get('max_shipping_days'),
                    min_rating=buyer_intent_data.get('min_rating'),
                    special_requirements=buyer_intent_data.get('special_requirements')
                )
                
                # Create checkout request
                checkout_request = CheckoutRequest(
                    product_id=data['product_id'],
                    quantity=data['quantity'],
                    buyer_intent=buyer_intent
                )
                
                # Process checkout
                checkout_response = checkout_manager.create_checkout_session(checkout_request)
                
                # Convert to dict for JSON response
                session = checkout_response.session
                response_data = {
                    "session": {
                        "session_id": session.session_id,
                        "line_item": {
                            "product_id": session.line_item.product_id,
                            "product_name": session.line_item.product_name,
                            "quantity": session.line_item.quantity,
                            "unit_price": session.line_item.unit_price,
                            "total_price": session.line_item.total_price
                        },
                        "shipping_option": {
                            "method": session.shipping_option.method,
                            "eta_days": session.shipping_option.eta_days,
                            "cost": session.shipping_option.cost
                        },
                        "subtotal": session.subtotal,
                        "tax": session.tax,
                        "total": session.total,
                        "checkout_status": session.checkout_status,
                        "approval_status": session.approval_status,
                        "created_at": session.created_at.isoformat(),
                        "updated_at": session.updated_at.isoformat(),
                        "approval_risk_factors": session.approval_risk_factors
                    },
                    "requires_approval": checkout_response.requires_approval,
                    "approval_risk_factors": checkout_response.approval_risk_factors
                }
                
                self._send_json_response(response_data)
            
            elif path.startswith('/checkout/session/') and path.endswith('/complete'):
                session_id = path.split('/')[-2]
                try:
                    success = checkout_manager.complete_checkout_session(session_id)
                    if success:
                        self._send_json_response({"success": True, "message": "Checkout completed successfully"})
                    else:
                        self._send_error("Failed to complete checkout", 400)
                except ValueError as e:
                    # Handle validation errors (like unapproved sessions) as 400
                    self._send_error(str(e), 400)
                except Exception as e:
                    # Handle other errors as 500
                    self._send_error(f"Internal error: {str(e)}", 500)
            
            elif path == '/agent/shop':
                # Handle buyer agent shopping request (mock for smoke test)
                user_request = data.get('user_request', '')
                if not user_request:
                    self._send_error("User request is required", 400)
                    return
                
                if not user_request.strip():
                    self._send_error("User request cannot be empty", 400)
                    return
                
                try:
                    # Create a mock checkout session for smoke testing
                    
                    # Get max_budget from request and select product accordingly
                    max_budget = data.get('max_budget')
                    products = catalog_manager.get_all_products()
                    demo_product = None
                    budget_match = True
                    
                    if max_budget and max_budget > 0:
                        # Find best product under budget
                        for product in products:
                            if product.price <= max_budget:
                                if demo_product is None or product.price > demo_product.price:
                                    demo_product = product
                        
                        # If no product under budget, find closest option
                        if not demo_product:
                            demo_product = min(products, key=lambda p: p.price)
                            budget_match = False
                    else:
                        # No budget specified, use executive briefcase for demo
                        for product in products:
                            if "executive" in product.name.lower() and "briefcase" in product.name.lower():
                                demo_product = product
                                break
                        
                        if not demo_product:
                            demo_product = products[0]  # Fallback to first product
                    
                    # Create mock buyer intent
                    buyer_intent = BuyerIntent(
                        max_price=max_budget if max_budget and max_budget > 0 else 150.0,
                        category="laptop_bag",
                        max_shipping_days=7,
                        special_requirements=f"Request: {user_request}"
                    )
                    
                    # Create checkout request
                    checkout_request = CheckoutRequest(
                        product_id=demo_product.id,
                        quantity=1,
                        buyer_intent=buyer_intent
                    )
                    
                    # Process checkout
                    result = checkout_manager.create_checkout_session(checkout_request)
                    session = result.session
                    
                    # Format response for UI
                    response_data = {
                        "success": True,
                        "selected_product": {
                            "id": demo_product.id,
                            "name": demo_product.name,
                            "price": demo_product.price,
                            "short_description": demo_product.short_description,
                            "shipping_eta_days": demo_product.shipping_eta_days
                        },
                        "checkout_session": {
                            "session": {
                                "session_id": session.session_id,
                                "subtotal": session.subtotal,
                                "total": session.total,
                                "tax": session.tax,
                                "shipping_option": {
                                    "method": session.shipping_option.method,
                                    "cost": session.shipping_option.cost
                                },
                                "approval_risk_factors": session.approval_risk_factors
                            },
                            "approval_required": session.approval_status == "pending"
                        },
                        "approval_required": session.approval_status == "pending",
                        "budget_match": budget_match
                    }
                    
                    # Add budget warning if no match found
                    if not budget_match:
                        response_data["budget_message"] = f"No products found within ${max_budget:.2f} budget; showing closest available option."
                    self._send_json_response(response_data)
                    
                except Exception as e:
                    self._send_json_response({
                        "success": False,
                        "error_message": str(e)
                    })
            
                        
            elif path.startswith('/agent/approvals/') and path.endswith('/approve'):
                approval_id = path.split('/')[-2]
                # Extract session_id from approval_id (format: approval_session_xxx)
                session_id = approval_id.replace("approval_", "")
                print(f"DEBUG: Approving session {session_id}")
                try:
                    success = checkout_manager.approve_checkout_session(session_id, True, "system", "Test approval")
                    print(f"DEBUG: Approval success = {success}")
                    if success:
                        self._send_json_response({"message": "Approval granted successfully"})
                    else:
                        self._send_error("Failed to grant approval", 400)
                except Exception as e:
                    print(f"DEBUG: Approval error = {str(e)}")
                    self._send_error(f"Approval error: {str(e)}", 500)
            
            elif path.startswith('/agent/approvals/') and path.endswith('/reject'):
                approval_id = path.split('/')[-2]
                # Extract session_id from approval_id (format: approval_session_xxx)
                session_id = approval_id.replace("approval_", "")
                print(f"DEBUG: Rejecting session {session_id}")
                try:
                    success = checkout_manager.approve_checkout_session(session_id, False, "system", "Test rejection")
                    print(f"DEBUG: Rejection success = {success}")
                    if success:
                        self._send_json_response({"message": "Approval rejected successfully"})
                    else:
                        self._send_error("Failed to reject approval", 400)
                except Exception as e:
                    print(f"DEBUG: Rejection error = {str(e)}")
                    self._send_error(f"Rejection error: {str(e)}", 500)
            
            else:
                self._send_error("Not found", 404)
                
        except Exception as e:
            self._send_error(str(e))


def run_server():
    """Run the HTTP server."""
    # Initialize catalog on startup
    try:
        catalog_manager._load_catalog()
        print(f"Catalog loaded with {len(catalog_manager.get_all_products())} products")
    except Exception as e:
        print(f"Failed to load catalog: {e}")
    
    # Run server
    import os
    port = int(os.getenv("PORT", "8000"))
    server_address = ('', port)
    httpd = HTTPServer(server_address, CommerceHandler)
    print(f"Starting server on port {port}")
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()
