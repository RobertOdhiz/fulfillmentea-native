import streamlit as st
import sys
import os

# Add dashboard root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import api_client

def login(phone: str, password: str) -> str:
    """Authenticate user and return JWT token"""
    try:
        data = api_client.post("/auth/login", {"phone": phone, "password": password})
        return data["access_token"]
    except Exception as e:
        st.error(f"Login failed: {str(e)}")
        return None

def ensure_auth():
    """Ensure user is authenticated, show login form if not"""
    if "token" not in st.session_state:
        with st.form("login"):
            st.subheader("🔐 Sign in to Fulfillmentea")
            phone = st.text_input("📱 Phone Number")
            password = st.text_input("🔒 Password", type="password")
            submitted = st.form_submit_button("Login", type="primary")
        
        if submitted:
            token = login(phone, password)
            if token:
                st.session_state.token = token
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Login failed. Please check your credentials.")
        st.stop()

def get_current_user(token: str):
    """Get current authenticated user info"""
    try:
        return api_client.get("/staff/me", token)
    except Exception as e:
        st.error(f"Failed to get user info: {str(e)}")
        return None

def check_role_access(token: str, allowed_roles: set):
    """Check if current user has required role access"""
    try:
        user = get_current_user(token)
        return user and user.get("role") in allowed_roles
    except:
        return False

def logout():
    """Logout user and clear session state"""
    if "token" in st.session_state:
        del st.session_state.token
    if "user" in st.session_state:
        del st.session_state.user
    st.rerun()