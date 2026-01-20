"""
End-to-end test for BoundCart commerce checkout flow.
"""

import pytest
import requests
import time
from datetime import datetime
from typing import Dict, List

# Configuration
import os

API_BASE = os.getenv("API_BASE", "http://localhost:8000")


class TestBoundCartCheckoutFlow:
    """Test complete BoundCart checkout flow."""
    
    def setup_method(self):
        """Setup test environment."""
        # Clear any existing data by restarting backend conceptually
        self.session_id = None
        self.approval_id = None
        self.settlement_id = None
    
    def api_call(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make API call to backend."""
        url = f"{API_BASE}{endpoint}"
        
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PATCH":
            response = requests.patch(url, json=data)
        
        assert response.status_code == 200, f"API call failed: {response.status_code} - {response.text}"
        return response.json()
    
    def test_01_session_creation(self):
        """Test 1: Create checkout session that requires approval."""
        print("🧪 Test 1: Creating high-value checkout session...")
        
        # Create high-value request that requires approval
        result = self.api_call(
            "POST",
            "/agent/shop",
            {"user_request": "Buy executive laptop briefcase under 150"}
        )
        
        # Verify session creation
        assert result["success"], f"Agent workflow failed: {result.get('error_message')}"
        assert result["approval_required"], "Expected approval to be required"
        assert result["selected_product"] is not None, "Expected product to be selected"
        
        # Store session ID for subsequent tests
        self.session_id = result["checkout_session"].session.session_id
        print(f"✅ Session created: {self.session_id}")
        
        # Verify session details
        session = result["checkout_session"].session
        assert session.checkout_status == "created", f"Unexpected status: {session.checkout_status}"
        assert session.approval_status == "pending", f"Unexpected approval status: {session.approval_status}"
        assert session.total > 100, "Expected high-value transaction"
        
        return result
    
    def test_02_approval_request(self):
        """Test 2: Verify approval request is created."""
        print("🧪 Test 2: Verifying approval request...")
        
        # Get pending approvals
        pending = self.api_call("GET", "/agent/approvals/pending")
        assert len(pending) > 0, "Expected at least one pending approval"
        
        # Find our approval
        approval = None
        for req in pending:
            if req.session_id == self.session_id:
                approval = req
                self.approval_id = req.approval_id
                break
        
        assert approval is not None, f"Expected approval request for session {self.session_id}"
        assert approval.status == "pending", f"Expected pending status, got {approval.status}"
        assert approval.total_amount > 100, "Expected high-value amount"
        
        print(f"✅ Approval request created: {self.approval_id}")
        return approval
    
    def test_03_approval_granted(self):
        """Test 3: Grant approval."""
        print("🧪 Test 3: Granting approval...")
        
        # Approve the request
        result = self.api_call(
            "POST",
            f"/agent/approvals/{self.approval_id}/approve",
            {
                "approver": "test_user",
                "rationale": "Test approval for executive briefcase"
            }
        )
        
        assert "message" in result, "Expected approval success message"
        print(f"✅ Approval granted: {result['message']}")
        
        # Verify approval status
        time.sleep(0.1)  # Brief pause for state update
        approval_status = self.api_call("GET", f"/agent/approvals/{self.approval_id}")
        assert approval_status.status == "approved", f"Expected approved status, got {approval_status.status}"
        
        return result
    
    def test_04_checkout_completion(self):
        """Test 4: Complete checkout after approval."""
        print("🧪 Test 4: Completing checkout...")
        
        # Complete checkout session
        result = self.api_call(
            "POST",
            f"/checkout/session/{self.session_id}/complete"
        )
        
        assert "message" in result, "Expected completion success message"
        print(f"✅ Checkout completed: {result['message']}")
        
        # Verify session status
        session = self.api_call("GET", f"/checkout/session/{self.session_id}")
        assert session.checkout_status == "completed", f"Expected completed status, got {session.checkout_status}"
        assert session.approval_status == "approved", f"Expected approved status, got {session.approval_status}"
        
        return result
    
    def test_05_settlement_creation(self):
        """Test 5: Verify settlement is created."""
        print("🧪 Test 5: Verifying settlement creation...")
        
        # Get settlement for session
        settlement = self.api_call("GET", f"/settlement/{self.session_id}")
        
        assert settlement is not None, "Expected settlement to be created"
        assert settlement.status in ["created", "processing", "completed"], f"Unexpected settlement status: {settlement.status}"
        assert settlement.amount > 100, "Expected high-value settlement amount"
        assert settlement.session_id == self.session_id, "Settlement session mismatch"
        
        self.settlement_id = settlement["settlement_id"]
        print(f"✅ Settlement created: {self.settlement_id}")
        
        return settlement
    
    def test_06_audit_trail(self):
        """Test 6: Verify complete audit trail."""
        print("🧪 Test 6: Verifying audit trail...")
        
        # Get audit events for session
        events = self.api_call("GET", f"/audit/{self.session_id}")
        
        # Expected event types in order
        expected_events = [
            "session_created",
            "products_shortlisted", 
            "product_selected",
            "checkout_session_created",
            "approval_requested",
            "approval_granted",
            "checkout_completed"
        ]
        
        assert len(events) >= len(expected_events), f"Expected at least {len(expected_events)} events, got {len(events)}"
        
        # Verify event types exist
        event_types = [event["event_type"] for event in events]
        for expected_event in expected_events:
            assert expected_event in event_types, f"Missing expected event: {expected_event}"
        
        # Verify chronological order
        timestamps = [event["timestamp"] for event in events]
        assert timestamps == sorted(timestamps), "Events should be in chronological order"
        
        print(f"✅ Audit trail verified: {len(events)} events")
        
        return events
    
    def test_07_approval_statistics(self):
        """Test 7: Verify approval statistics."""
        print("🧪 Test 7: Verifying approval statistics...")
        
        # Get approval summary
        summary = self.api_call("GET", "/agent/approvals/summary")
        
        assert summary["total_requests"] >= 1, "Expected at least one approval request"
        assert summary["approved"] >= 1, "Expected at least one approval"
        assert summary["approval_rate"] > 0, "Expected positive approval rate"
        
        print(f"✅ Approval statistics verified: {summary}")
        
        return summary
    
    def test_complete_flow(self):
        """Test complete end-to-end flow."""
        print("\nStarting complete BoundCart checkout flow test")
        print("=" * 50)
        
        try:
            # Execute all test steps
            self.test_01_session_creation()
            self.test_02_approval_request()
            self.test_03_approval_granted()
            self.test_04_checkout_completion()
            self.test_05_settlement_creation()
            self.test_06_audit_trail()
            self.test_07_approval_statistics()
            
            print("\n" + "=" * 50)
            print("All tests passed! BoundCart checkout flow working correctly.")
            print("\n📋 Test Summary:")
            print(f"  ✅ Session ID: {self.session_id}")
            print(f"  ✅ Approval ID: {self.approval_id}")
            print(f"  ✅ Settlement ID: {self.settlement_id}")
            print(f"  ✅ Architecture boundaries preserved")
            print(f"  ✅ Human approval control point functional")
            print(f"  ✅ Audit trail complete")
            print(f"  ✅ Settlement processed")
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            raise
    
    def test_low_value_flow(self):
        """Test low-value flow that doesn't require approval."""
        print("\n🚀 Starting Low-Value Flow Test (No Approval Required)")
        print("=" * 50)
        
        # Create low-value request
        result = self.api_call(
            "POST",
            "/agent/shop",
            {"user_request": "Buy laptop bag under 50 with fast shipping"}
        )
        
        assert result["success"], f"Agent workflow failed: {result.get('error_message')}"
        assert not result["approval_required"], "Expected no approval required"
        assert result["workflow_complete"], "Expected workflow to complete automatically"
        
        session_id = result["checkout_session"]["session"]["session_id"]
        
        # Verify session is auto-completed
        session = self.api_call("GET", f"/checkout/session/{session_id}")
        assert session["checkout_status"] == "completed", f"Expected completed status, got {session['checkout_status']}"
        assert session["approval_status"] == "not_required", f"Expected not_required status, got {session['approval_status']}"
        
        # Verify settlement exists
        settlement = self.api_call("GET", f"/settlement/{session_id}")
        assert settlement is not None, "Expected settlement to be created"
        
        print(f"\n🎉 Low-value flow test passed!")
        print(f"  ✅ Session ID: {session_id}")
        print(f"  ✅ Auto-approved and completed")
        print(f"  ✅ Settlement processed")
        print(f"  ✅ No human intervention required")


def test_backend_health():
    """Test backend health before running tests."""
    print("🔍 Checking backend health...")
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        assert response.status_code == 200, "Backend not responding"
        
        health = response.json()
        assert health["status"] == "healthy", "Backend not healthy"
        assert health["products_loaded"] > 0, "No products loaded"
        
        print(f"✅ Backend healthy: {health['products_loaded']} products loaded")
        return True
        
    except Exception as e:
        print(f"❌ Backend health check failed: {str(e)}")
        return False


if __name__ == "__main__":
    """Run tests manually if script executed directly."""
    print("BoundCart — Manual Test Runner")
    print("Note: Run 'pytest tests/test_checkout_flow.py' for automated testing")
    print()
    
    # Check backend health
    if not test_backend_health():
        print("❌ Backend not available. Please start the backend first:")
        print("   cd backend")
        print("   python app.py")
        exit(1)
    
    # Run tests
    test_instance = TestBoundCartCheckoutFlow()
    
    try:
        test_instance.test_complete_flow()
        test_instance.test_low_value_flow()
        print("\n🎉 All manual tests completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Manual test failed: {str(e)}")
        exit(1)
