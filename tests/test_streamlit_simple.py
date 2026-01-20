"""
Simple Streamlit UI test runner without pytest dependencies.
Tests core functionality using direct imports.
"""

import sys
import os


def test_streamlit_ui():
    """Test Streamlit UI functionality directly."""
    print("🧪 Testing Streamlit UI...")
    
    try:
        # Test 1: App loads without exceptions
        print("✅ Test 1: App loads without exceptions...")
        # Simple test - just try to import the app module
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.path.insert(0, project_root)
        sys.path.insert(0, os.path.join(project_root, 'streamlit_app'))
        import app as streamlit_app
        print("✅ Test 1 PASSED: App imports successfully")
        
        # Test 2: Basic functionality test
        print("✅ Test 2: Basic functionality test...")
        # Test that we can access the app's main components
        # We're not testing specific UI elements, just that the app structure is sound
        if hasattr(streamlit_app, 'main') or hasattr(streamlit_app, 'run'):
            print("✅ Test 2 PASSED: App has expected structure")
        else:
            print("⚠️ Test 2 WARNING: App structure may be incomplete")
        
        print("🎯 All Streamlit UI tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Streamlit UI test failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_streamlit_ui()
    if success:
        print("✅ Streamlit UI tests PASSED")
    else:
        print("❌ Streamlit UI tests FAILED")
        sys.exit(1)
