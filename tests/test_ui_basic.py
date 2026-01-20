"""
Basic Streamlit UI test - minimal approach.
Tests that the app can be imported and has basic structure.
"""

def test_basic_ui():
    """Test basic Streamlit UI functionality."""
    print("🧪 Testing Basic Streamlit UI...")
    
    try:
        # Test that we can import the app module
        import sys
        import os
        
        # Add project root to path
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.path.insert(0, project_root)
        
        # Import app
        import streamlit_app.app as app
        print("✅ Import test PASSED: App module imported successfully")
        
        # Test that app has expected structure
        if hasattr(app, 'main'):
            print("✅ Structure test PASSED: App has main function")
        else:
            print("⚠️ Structure test WARNING: App missing main function")
        
        print("🎯 Basic UI test completed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import test FAILED: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Basic UI test FAILED: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_basic_ui()
    if success:
        print("✅ Streamlit UI tests PASSED")
    else:
        print("❌ Streamlit UI tests FAILED")
