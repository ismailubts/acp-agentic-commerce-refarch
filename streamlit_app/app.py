"""
BoundCart Streamlit demo — governed agent commerce oversight UI.
"""

import streamlit as st
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
def get_api_base():
    """Get API base URL with deployment-safe fallbacks."""
    import os
    try:
        # Try Streamlit secrets first (safe access, handles missing secrets file)
        base = st.secrets.get("API_BASE")
        if base:
            return base
    except Exception:
        # Secrets file doesn't exist or other secret access error
        pass
    # Fall back to environment variable
    env_base = os.getenv("API_BASE")
    if env_base:
        return env_base
    # Finally fall back to local development default
    return "http://localhost:8000"

# Helper functions
def normalize_checkout_session_for_state(session_data, existing_state=None):
    """Normalize session data to wrapped shape for Streamlit state."""
    if not session_data:
        return None

    if "session" in session_data and isinstance(session_data["session"], dict):
        return session_data

    normalized = {"session": session_data}

    if existing_state and isinstance(existing_state, dict):
        for key in ("requires_approval", "approval_risk_factors"):
            if key in existing_state:
                normalized[key] = existing_state[key]

    return normalized

def api_call(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
    """Make API call to backend."""
    try:
        api_base = get_api_base()  # Dynamic resolution for deployment
        url = f"{api_base}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PATCH":
            response = requests.patch(url, json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return {}

def format_currency(amount: float) -> str:
    """Format amount as currency."""
    return f"${amount:.2f}"

def format_timestamp(timestamp: str) -> str:
    """Format timestamp for display."""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp

# Initialize session state
if 'current_session' not in st.session_state:
    st.session_state.current_session = None
if 'approval_requests' not in st.session_state:
    st.session_state.approval_requests = []
if 'workflow_result' not in st.session_state:
    st.session_state.workflow_result = None

# Main UI
st.set_page_config(
    page_title="BoundCart",
    page_icon="◈",
    layout="wide"
)

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(1200px 600px at 10% -10%, #d8efe8 0%, transparent 55%),
            radial-gradient(900px 500px at 100% 0%, #f3e6d4 0%, transparent 50%),
            linear-gradient(180deg, #f7faf8 0%, #eef3f0 45%, #f8f6f2 100%);
        color: #1a2e28;
        font-family: "Segoe UI", "Trebuchet MS", sans-serif;
    }

    h1, h2, h3 {
        font-family: Georgia, "Palatino Linotype", "Book Antiqua", serif !important;
        letter-spacing: -0.02em;
        color: #14352c !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #14352c 0%, #1c4a3d 55%, #245a4a 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    [data-testid="stSidebar"] * {
        color: #e8f2ee !important;
    }

    [data-testid="stSidebar"] .stTextArea textarea,
    [data-testid="stSidebar"] .stNumberInput input {
        background: rgba(255,255,255,0.08) !important;
        color: #f4faf7 !important;
        border: 1px solid rgba(255,255,255,0.18) !important;
        border-radius: 10px !important;
    }

    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown p {
        color: #c5ddd4 !important;
    }

    div.stButton > button[kind="primary"] {
        background: #c4a574 !important;
        color: #14352c !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        box-shadow: 0 8px 20px rgba(20, 53, 44, 0.18);
    }

    div.stButton > button[kind="primary"]:hover {
        background: #d4b888 !important;
    }

    div.stButton > button:not([kind="primary"]) {
        border-radius: 10px !important;
        border: 1px solid #b7cfc5 !important;
        background: #ffffffaa !important;
    }

    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.72);
        border: 1px solid #d5e4dd;
        border-radius: 14px;
        padding: 0.75rem 1rem;
    }

    .boundcart-hero {
        padding: 0.2rem 0 0.8rem 0;
    }

    .boundcart-brand {
        font-family: Georgia, "Palatino Linotype", "Book Antiqua", serif;
        font-size: 2.75rem;
        line-height: 1.05;
        color: #14352c;
        margin: 0;
    }

    .boundcart-tag {
        margin-top: 0.35rem;
        color: #3d5c52;
        font-size: 1.05rem;
        max-width: 42rem;
    }

    .boundcart-rule {
        height: 2px;
        width: 100%;
        margin: 1rem 0 1.25rem 0;
        background: linear-gradient(90deg, #c4a574 0%, #245a4a 40%, transparent 100%);
        border: 0;
    }

    .boundcart-footer {
        text-align: center;
        color: #5a7268;
        font-size: 0.85rem;
        padding: 1.25rem 0 0.5rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="boundcart-hero">
      <p class="boundcart-brand">BoundCart</p>
      <p class="boundcart-tag">Governed agent commerce — shop autonomously, approve what matters, leave a clear trail.</p>
    </div>
    <div class="boundcart-rule"></div>
    """,
    unsafe_allow_html=True,
)

# Sidebar for user input
with st.sidebar:
    st.header("Shopping request")
    
    # Shopping request input
    user_request = st.text_area(
        "Describe what you want to buy:",
        placeholder="e.g., 'I need a laptop bag under $120 with fast shipping'",
        height=100,
        help="Be specific about price limits, shipping preferences, and product features"
    )
    
    # Budget input
    budget = st.number_input(
        "Maximum budget (optional):",
        min_value=0.0,
        step=1.00,
        help="Set a hard budget limit - will override any amount mentioned in your request"
    )
    
    # Run agent button
    if st.button("Run shopping agent", type="primary"):
        if not user_request.strip():
            st.error("Please describe what you want to buy")
        elif budget == 0:
            st.warning("No budget specified - system will use default limits")
            # Continue anyway
            with st.spinner("Analyzing your shopping request..."):
                # Call buyer agent
                result = api_call(
                    "POST",
                    "/agent/shop",
                    {"user_request": user_request, "max_budget": budget}
                )
                
                if result.get("success"):
                    st.session_state.workflow_result = result
                    st.session_state.current_session = normalize_checkout_session_for_state(
                        result.get("checkout_session"),
                        st.session_state.current_session,
                    )
                    
                    # Refresh pending approvals
                    approvals = api_call("GET", "/agent/approvals/pending")
                    st.session_state.approval_requests = approvals if approvals else []
                    
                    st.rerun()
                else:
                    st.error(f"Shopping request failed: {result.get('error_message', 'Unknown error')}")
        else:
            with st.spinner("Analyzing your shopping request..."):
                # Call buyer agent
                result = api_call(
                    "POST",
                    "/agent/shop",
                    {"user_request": user_request, "max_budget": budget}
                )
                
                if result.get("success"):
                    st.session_state.workflow_result = result
                    st.session_state.current_session = normalize_checkout_session_for_state(
                        result.get("checkout_session"),
                        st.session_state.current_session,
                    )
                    
                    # Refresh pending approvals
                    approvals = api_call("GET", "/agent/approvals/pending")
                    st.session_state.approval_requests = approvals if approvals else []
                    
                    st.rerun()
                else:
                    st.error(f"Shopping request failed: {result.get('error_message', 'Unknown error')}")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Workflow results")
    
    if st.session_state.workflow_result:
        result = st.session_state.workflow_result
        
        # Success/Error status
        if result.get("success"):
            st.success("Workflow completed successfully")
            
            # Selected product
            if result.get("selected_product"):
                product = result["selected_product"]
                st.subheader("Selected product")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Name", product["name"])
                with col_b:
                    st.metric("Price", format_currency(product["price"]))
                with col_c:
                    st.metric("Shipping", f"{product['shipping_eta_days']} days")
                
                st.text(product["short_description"])
            
            # Checkout session
            if result.get("checkout_session"):
                session = result["checkout_session"]["session"]
                st.subheader("Checkout session")
                
                col_d, col_e, col_f = st.columns(3)
                with col_d:
                    st.metric("Session ID", session["session_id"])
                with col_e:
                    st.metric("Subtotal", format_currency(session["subtotal"]))
                with col_f:
                    st.metric("Total", format_currency(session["total"]))
                
                # Shipping details
                st.write("**Shipping option:**", session["shipping_option"]["method"])
                st.write("**Shipping cost:**", format_currency(session["shipping_option"]["cost"]))
                st.write("**Tax:**", format_currency(session["tax"]))
            
            # Approval status
            if result.get("approval_required"):
                st.warning("Human approval required")
                st.write("This transaction needs manual approval before checkout can finish.")
                
                # Show risk factors
                if result["checkout_session"].get("approval_risk_factors"):
                    st.write("**Why approval is needed:**")
                    for factor in result["checkout_session"]["approval_risk_factors"]:
                        st.write(f" {factor}")
                st.info("Review this request in the Approval desk on the right.")
            else:
                st.success("Automatically approved")
                st.write("This transaction meets the rules and can proceed to checkout.")
                
        else:
            st.error("Shopping request failed")
            if result.get("error_message"):
                st.error(f"Error details: {result['error_message']}")
            st.info("Please check your request and try again.")
    else:
        st.info("Start with a shopping request in the sidebar.")

with col2:
    st.header("Approval desk")
    
    # Pending approvals
    if st.session_state.approval_requests:
        st.subheader("Pending")
        
        for approval in st.session_state.approval_requests:
            product_name = approval.get('product_name', 'Unknown Product')
            with st.expander(f"Review: {product_name}", expanded=True):
                st.write(f"**Product:** {product_name}")
                st.write(f"**Total amount:** {format_currency(approval.get('total_amount', 0))}")
                st.write(f"**Request ID:** {approval.get('session_id', 'Unknown')}")
                
                if approval.get('risk_factors'):
                    st.write("**Review required because:**")
                    for factor in approval['risk_factors']:
                        st.write(f" {factor}")
                
                # Approval buttons
                st.write("**Take action:**")
                col_approve, col_reject = st.columns(2)
                with col_approve:
                    if st.button("Approve", key=f"approve_{approval['approval_id']}", help="Approve this purchase request"):
                        with st.spinner("Processing approval..."):
                            api_result = api_call(
                                "POST",
                                f"/agent/approvals/{approval['approval_id']}/approve",
                                {
                                    "approver": "demo_user",
                                    "rationale": "Approved via demo interface"
                                }
                            )
                            if api_result:
                                st.success("Purchase approved!")
                                # Refresh session data after approval
                                if st.session_state.current_session:
                                    session_id = st.session_state.current_session["session"]["session_id"]
                                    try:
                                        api_base = get_api_base()  # Dynamic resolution for deployment
                                        refreshed_response = requests.get(f"{api_base}/checkout/session/{session_id}")
                                        if refreshed_response.status_code == 200:
                                            refreshed_session = refreshed_response.json()
                                            st.session_state.current_session = normalize_checkout_session_for_state(
                                                refreshed_session,
                                                st.session_state.current_session,
                                            )
                                        else:
                                            st.error("Failed to refresh session data after approval")
                                    except Exception as e:
                                        st.error(f"Error refreshing session: {str(e)}")
                                st.rerun()
                            else:
                                st.error("Approval failed - please try again")
                
                with col_reject:
                    if st.button("Reject", key=f"reject_{approval['approval_id']}", help="Reject this purchase request"):
                        with st.spinner("Processing rejection..."):
                            api_result = api_call(
                                "POST",
                                f"/agent/approvals/{approval['approval_id']}/reject",
                                {
                                    "approver": "demo_user",
                                    "rationale": "Rejected via demo interface"
                                }
                            )
                            if api_result:
                                st.error("Purchase rejected!")
                                st.rerun()
                            else:
                                st.error("Rejection failed - please try again")
    else:
        st.info("No pending approvals")
    
    # Approval summary
    st.subheader("Approval stats")
    summary = api_call("GET", "/agent/approvals/summary")
    if summary:
        col_total, col_pending, col_approved, col_rejected = st.columns(4)
        with col_total:
            st.metric("Total", summary.get("total_requests", 0))
        with col_pending:
            st.metric("Pending", summary.get("pending", 0))
        with col_approved:
            st.metric("Approved", summary.get("approved", 0))
        with col_rejected:
            st.metric("Rejected", summary.get("rejected", 0))

# Bottom section for audit trail and settlement
st.markdown('<div class="boundcart-rule"></div>', unsafe_allow_html=True)

audit_col, settlement_col = st.columns(2)

with audit_col:
    st.header("Audit timeline")
    
    if st.session_state.current_session:
        session_id = st.session_state.current_session["session"]["session_id"]
        audit_events = api_call("GET", f"/audit/{session_id}")
        
        if audit_events:
            # Sort events by timestamp (newest first for better UX)
            sorted_events = sorted(audit_events, key=lambda x: x['timestamp'], reverse=True)
            
            st.write(f"Showing {len(sorted_events)} events for this transaction:")
            
            for i, event in enumerate(sorted_events):
                with st.expander(f" {format_timestamp(event['timestamp'])} - {event['event_type'].replace('_', ' ').title()}", expanded=(i == 0)):
                    st.write(f"**Who:** {event['actor']}")
                    st.write(f"**Action:** {event['event_type'].replace('_', ' ').title()}")
                    if event.get('details'):
                        st.write("**Details:**")
                        for key, value in event['details'].items():
                            st.write(f"  {key.replace('_', ' ').title()}: {value}")
        else:
            st.info("No audit events available for this session")
    else:
        st.info("Complete a shopping request to view the audit trail")

with settlement_col:
    st.header("Settlement")
    
    if st.session_state.current_session:
        session_id = st.session_state.current_session["session"]["session_id"]
        # Handle settlement call specially to avoid showing 404 as error
        try:
            api_base = get_api_base()  # Dynamic resolution for deployment
            url = f"{api_base}/settlement/{session_id}"
            response = requests.get(url)
            if response.status_code == 200:
                settlement = response.json()
            elif response.status_code == 404:
                # Normal pre-settlement state, handle gracefully
                settlement = None
            else:
                # Genuine error
                st.error(f"API Error: {response.status_code} - {response.text}")
                settlement = None
        except Exception as e:
            st.error(f"Connection Error: {str(e)}")
            settlement = None
        
        if settlement:
            st.subheader("Settlement details")
            col_settle_id, col_amount, col_status = st.columns(3)
            with col_settle_id:
                st.metric("Settlement ID", settlement["settlement_id"])
            with col_amount:
                st.metric("Amount", format_currency(settlement["amount"]))
            with col_status:
                st.metric("Status", settlement["status"].replace("_", " ").title())
            
            st.write(f"**Provider:** {settlement['provider']}")
            st.write(f"**Created:** {format_timestamp(settlement['created_at'])}")
            
            if settlement.get("completed_at"):
                st.write(f"**Completed:** {format_timestamp(settlement['completed_at'])}")
        else:
            # Handle pre-settlement state gracefully
            session_status = st.session_state.current_session["session"].get("checkout_status", "unknown")
            session_id = st.session_state.current_session["session"]["session_id"]
            
            if session_status == "approved":
                st.info("Ready for checkout completion")
                if st.button("Complete checkout", key="complete_checkout", help="Complete the approved checkout and create settlement"):
                    with st.spinner("Completing checkout..."):
                        print(f"DEBUG: Attempting completion for session {session_id}")
                        completion_result = api_call("POST", f"/checkout/session/{session_id}/complete")
                        print(f"DEBUG: Completion result: {completion_result}")
                        if completion_result and completion_result.get("success"):
                            st.success("Checkout completed! Settlement created.")
                            print(f"DEBUG: Completion successful, rerunning UI")
                            st.rerun()
                        else:
                            st.error("Checkout completion failed - please try again")
                            print(f"DEBUG: Completion failed: {completion_result}")
            elif session_status == "completed":
                st.warning("Settlement processing...")
            else:
                st.info("Settlement appears after approval and completion")
    else:
        st.info("Complete a shopping request to view settlement")

# Footer
st.markdown(
    """
    <div class="boundcart-footer">
        BoundCart · Governed Agent Commerce · Demo build
    </div>
    """,
    unsafe_allow_html=True
)
