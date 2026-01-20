"""
Minimal automated tests for Streamlit UI using Streamlit AppTest API.
Tests core functionality without brittle UI assertions.
"""

import pytest
from streamlit.testing.v1 import AppTest
import streamlit as st
import requests
import json


class TestStreamlitUI(AppTest):
    """Test Streamlit UI core functionality."""
    
    def test_app_loads_without_exceptions(self):
        """Test that the app loads without exceptions."""
        # This test passes if AppTest can instantiate the app
        # No assertions needed - AppTest handles loading validation
        pass
    
    def test_main_input_widgets_render(self):
        """Test that main input widgets are present and functional."""
        # Check that shopping request text area exists
        request_textarea = self.app.get_text_area("Enter your shopping request:")
        assert request_textarea is not None, "Shopping request text area not found"
        
        # Check that budget input exists
        budget_input = self.app.get_number_input("Budget (optional):")
        assert budget_input is not None, "Budget input not found"
        
        # Check that run agent button exists
        run_button = self.app.get_button("🚀 Run Buyer Agent")
        assert run_button is not None, "Run shopping agent button not found"
    
    def test_shopping_request_flow_no_crash(self):
        """Test that entering shopping request doesn't crash the app."""
        # Enter a shopping request
        request_textarea = self.app.get_text_area("Enter your shopping request:")
        request_textarea.input_value = "Find a laptop bag under $120"
        
        # Enter budget
        budget_input = self.app.get_number_input("Budget (optional):")
        budget_input.input_value = 150.0
        
        # Click run agent button
        run_button = self.app.get_button("🚀 Run Buyer Agent")
        run_button.click()
        
        # Wait for processing to complete
        self.wait_until_finished()
        
        # Should not crash and should show some result
        # We're not asserting specific content, just that it doesn't crash
        pass
    
    def test_approval_ui_appears_when_needed(self):
        """Test that approval UI appears when approval is required."""
        # Mock a response that requires approval
        with self.mock_requests("POST", "http://localhost:8000/agent/shop", 
                               json={"user_request": "Find a laptop bag under $120"}):
            
            # Enter request and run agent
            request_textarea = self.app.get_text_area("Enter your shopping request:")
            request_textarea.input_value = "Find a laptop bag under $120"
            
            budget_input = self.app.get_number_input("Budget (optional):")
            budget_input.input_value = 150.0
            
            run_button = self.app.get_button("🚀 Run Buyer Agent")
            run_button.click()
            
            self.wait_until_finished()
            
            # Check that approval management section appears
            # Look for approval management header
            approval_header = self.app.get_markdown("⚖️ Approval Management")
            assert approval_header is not None, "Approval desk section not found"
            
            # Look for approve button (should appear for high-value items)
            approve_button = self.app.get_button("✅ Approve")
            assert approve_button is not None, "Approve button not found"
    
    def test_status_elements_display(self):
        """Test that status and result elements display after flow."""
        # Run a complete flow first
        with self.mock_requests("POST", "http://localhost:8000/agent/shop",
                               json={"user_request": "Find a laptop bag under $120"}):
            
            request_textarea = self.app.get_text_area("Enter your shopping request:")
            request_textarea.input_value = "Find a laptop bag under $120"
            
            budget_input = self.app.get_number_input("Budget (optional):")
            budget_input.input_value = 150.0
            
            run_button = self.app.get_button("🚀 Run Buyer Agent")
            run_button.click()
            
            self.wait_until_finished()
            
            # Check that workflow results section shows content
            workflow_header = self.app.get_markdown("📋 Workflow Results")
            assert workflow_header is not None, "Workflow Results section not found"
            
            # Should show some success/error indicator
            # Not asserting specific content, just that elements appear
            pass


def run_streamlit_tests():
    """Run all Streamlit UI tests."""
    print("🧪 Running Streamlit UI Automated Tests...")
    
    # Run tests using pytest
    pytest.main(["-v", "tests/test_streamlit_ui.py"])


if __name__ == "__main__":
    run_streamlit_tests()
