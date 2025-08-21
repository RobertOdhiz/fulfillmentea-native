import streamlit as st
import sys
import os

# Add dashboard root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import PAGE_TITLE, PAGE_ICON, LAYOUT
from auth.login import ensure_auth, get_current_user, check_role_access
from pages.overview import render_overview
from pages.riders import render_riders
from pages.inventory import render_inventory
from pages.staff import render_staff
from pages.receipts import render_receipts
from pages.analytics import render_analytics


def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout=LAYOUT
    )
    
    # Ensure authentication
    ensure_auth()
    
    # Get current user
    me = get_current_user(st.session_state.token)
    print(f"Current User: {me}")
    role = me["role"]
    
    # Check role access
    allowed_roles = {"ADMIN", "SUPER_ADMIN", "MANAGER"}
    if role not in allowed_roles:
        st.error("You are not authorized to view this dashboard.")
        st.stop()
    
    # Sidebar
    st.sidebar.divider()
    
    # Navigation menu
    menu = st.sidebar.radio("Operations", [
        "Overview",
        "Manage Parcels",
        "Manage Riders", 
        "Manage Inventory",
        "Manage Staff",
        "Manage Receipts",
        "Analytics"
    ])
    
    # Render selected page
    if menu == "Overview":
        render_overview(st.session_state.token)
    elif menu == "Manage Parcels":
        from pages.parcels import render_parcel_management
        render_parcel_management(st.session_state.token)
    elif menu == "Manage Riders":
        render_riders(st.session_state.token)
    elif menu == "Manage Inventory":
        render_inventory(st.session_state.token)
    elif menu == "Manage Staff":
        render_staff(st.session_state.token)
    elif menu == "Manage Receipts":
        render_receipts(st.session_state.token)
    elif menu == "Analytics":
        render_analytics(st.session_state.token)
    
    # Footer
    st.sidebar.divider()
    st.sidebar.caption("Fulfillmentea Admin Dashboard v2.0")
    if st.sidebar.button("Logout"):
        del st.session_state.token


if __name__ == "__main__":
    main()
