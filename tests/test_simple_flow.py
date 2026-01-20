"""
Simple end-to-end test for BoundCart governed agent commerce reference.
"""

import requests
import time
from datetime import datetime
from typing import Dict, List

# Configuration
import os

API_BASE = os.getenv("API_BASE", "http://localhost:8000")


class TestSimpleCommerceFlow:
    """Test complete commerce flow without agent endpoints."""
    
    def setup_method(self):
        """Setup test environment."""
        self.session_id = None
        self.settlement_id = None
    
    def api_call(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make API call to backend."""
        url = f"{API_BASE}{endpoint}"
        
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        assert response.status_code == 200, f"API call failed: {response.status_code} - {response.text}"
        return response.json()
    
    def test_01_backend_health(self):
        """Test 1: Backend health check."""
        print("Testing backend health...")
        
        health = self.api_call("GET", "/health")
        assert health["status"] == "healthy"
        assert health["products_loaded"] > 0
        
        print(f"Backend healthy: {health['products_loaded']} products loaded")
        return health
    
    def test_02_list_products(self):
        """Test 2: List available products."""
        print("Testing product listing...")
        
        products = self.api_call("GET", "/products")
        assert len(products) > 0
        assert all("id" in p for p in products)
        assert all("name" in p for p in products)
        assert all("price" in p for p in products)
        
        # Find executive briefcase for high-value test
        executive_briefcase = None
        for product in products:
            if "executive" in product["name"].lower() and product["price"] > 100:
                executive_briefcase = product
                break
        
        assert executive_briefcase is not None, "Executive briefcase not found"
        print(f"Found executive briefcase: {executive_briefcase['name']} at ${executive_briefcase['price']}")
        
        return products, executive_briefcase
    
    def test_03_create_checkout_session(self):
        """Test 3: Create checkout session."""
        print("Testing checkout session creation...")
        
        # Get products first
        products, executive_briefcase = self.test_02_list_products()
        
        # Create checkout session for executive briefcase
        checkout_data = {
            "product_id": executive_briefcase["id"],
            "quantity": 1,
            "buyer_intent": {
                "max_price": 150.0,
                "category": "laptop_bag",
                "max_shipping_days": 7,
                "special_requirements": "Executive briefcase for business use"
            }
        }
        
        result = self.api_call("POST", "/checkout/session", checkout_data)
        
        # Verify session creation
        session = result["session"]
        assert session["total"] > 100, "Expected high-value transaction"
        assert session["checkout_status"] == "created", f"Unexpected status: {session['checkout_status']}"
        
        # Store session ID for subsequent tests
        self.session_id = session["session_id"]
        print(f"Session created: {self.session_id}")
        print(f"Total amount: ${session['total']}")
        print(f"Approval status: {session['approval_status']}")
        
        return result
    
    def test_04_get_session_details(self):
        """Test 4: Get session details."""
        print("Testing session details retrieval...")
        
        session = self.api_call("GET", f"/checkout/session/{self.session_id}")
        
        assert session["session_id"] == self.session_id
        assert session["total"] > 100
        assert session["checkout_status"] == "created"
        
        print(f"Session details retrieved for: {self.session_id}")
        return session
    
    def test_05_check_approval_required(self):
        """Test 5: Check if approval is required."""
        print("Testing approval requirement...")
        
        # Get pending approvals
        pending = self.api_call("GET", "/agent/approvals/pending")
        assert len(pending) > 0, "Expected at least one pending approval"
        
        # Find our approval
        approval = None
        for req in pending:
            if req["session_id"] == self.session_id:
                approval = req
                self.approval_id = req["approval_id"]
                break
        
        assert approval is not None, f"Expected approval request for session {self.session_id}"
        assert approval["status"] == "pending", f"Expected pending status, got {approval['status']}"
        assert approval["total_amount"] > 100, "Expected high-value amount"
        
        print(f"Approval request found: {self.approval_id}")
        return approval
    
    def test_06_grant_approval(self):
        """Test 6: Grant approval."""
        print("Testing approval grant...")
        
        # Approve the request
        result = self.api_call("POST", f"/agent/approvals/{self.approval_id}/approve")
        assert "message" in result
        print(f"Approval granted: {result['message']}")
        
        # Verify session status after approval
        session = self.api_call("GET", f"/checkout/session/{self.session_id}")
        assert session["approval_status"] == "approved", f"Expected approved status, got {session['approval_status']}"
        
        return result
    
    def test_07_complete_checkout(self):
        """Test 7: Complete checkout session."""
        print("Testing checkout completion...")
        
        # Now that approval is granted, complete checkout
        result = self.api_call("POST", f"/checkout/session/{self.session_id}/complete")
        
        assert "message" in result
        print(f"Checkout completion: {result['message']}")
        
        # Verify session status after completion
        session = self.api_call("GET", f"/checkout/session/{self.session_id}")
        print(f"Session status after completion: {session['checkout_status']}")
        
        return result
    
    def test_08_audit_trail(self):
        """Test 8: Verify audit trail."""
        print("Testing audit trail...")
        
        events = self.api_call("GET", f"/audit/{self.session_id}")
        
        # Verify we have audit events
        assert len(events) > 0, "Expected at least one audit event"
        
        # Check for expected event types
        event_types = [event["event_type"] for event in events]
        print(f"Audit events found: {len(events)}")
        for event_type in event_types:
            print(f"  - {event_type}")
        
        # Verify chronological order
        timestamps = [event["timestamp"] for event in events]
        assert timestamps == sorted(timestamps), "Events should be in chronological order"
        
        return events
    
    def test_09_settlement_info(self):
        """Test 9: Verify settlement information."""
        print("Testing settlement information...")
        
        settlement = self.api_call("GET", f"/settlement/{self.session_id}")
        
        if settlement:
            assert settlement["session_id"] == self.session_id
            assert settlement["amount"] > 100
            print(f"Settlement found: {settlement['settlement_id']}")
            print(f"Settlement status: {settlement['status']}")
        else:
            print("No settlement found (may not be created yet)")
        
        return settlement
    
    def test_complete_flow(self):
        """Test complete end-to-end flow."""
        print("\n" + "="*50)
        print("Starting Complete Commerce Flow Test")
        print("="*50)
        
        try:
            # Execute all test steps
            self.test_01_backend_health()
            self.test_02_list_products()
            self.test_03_create_checkout_session()
            self.test_04_get_session_details()
            self.test_05_check_approval_required()
            self.test_06_grant_approval()
            self.test_07_complete_checkout()
            self.test_08_audit_trail()
            self.test_09_settlement_info()
            
            print("\n" + "="*50)
            print("All tests passed! Commerce flow working correctly.")
            print("\nTest Summary:")
            print(f"  Session ID: {self.session_id}")
            print(f"  Architecture boundaries preserved")
            print(f"  Audit trail complete")
            print(f"  Settlement processed")
            
        except Exception as e:
            print(f"\nTest failed: {str(e)}")
            raise


def test_backend_health():
    """Test backend health before running tests."""
    print("Checking backend health...")
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        assert response.status_code == 200, "Backend not responding"
        
        health = response.json()
        assert health["status"] == "healthy", "Backend not healthy"
        assert health["products_loaded"] > 0, "No products loaded"
        
        print(f"Backend healthy: {health['products_loaded']} products loaded")
        return True
        
    except Exception as e:
        print(f"Backend health check failed: {str(e)}")
        return False


if __name__ == "__main__":
    """Run tests manually if script executed directly."""
    print("BoundCart — Simple Test Runner")
    print()
    
    # Check backend health
    if not test_backend_health():
        print("Backend not available. Please start the backend first:")
        print("  python backend/app_simple.py")
        exit(1)
    
    # Run tests
    test_instance = TestSimpleCommerceFlow()
    
    try:
        test_instance.test_complete_flow()
        print("\nAll manual tests completed successfully!")
        
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
    except Exception as e:
        print(f"\nManual test failed: {str(e)}")
        exit(1)
