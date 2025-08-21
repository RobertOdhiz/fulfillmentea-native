import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.client import api_client

def format_currency(amount: float, currency: str) -> str:
    """Format currency amount"""
    return f"{currency} {amount:,.2f}"

def get_parcel_status_color(status: str) -> str:
    """Get color for parcel status"""
    status_colors = {
        "RECEIVED": "🟢",
        "PROCESSING": "🟡", 
        "IN_TRANSIT": "🔵",
        "ARRIVED_AT_HUB": "🟣",
        "OUT_FOR_DELIVERY": "🟠",
        "DELIVERY_ATTEMPTED": "🟤",
        "DELIVERED": "✅",
        "RETURNED": "❌",
        "CANCELLED": "⚫"
    }
    return status_colors.get(status, "⚪")

def create_parcel_form():
    """Form to create a new parcel"""
    st.subheader("📦 Create New Parcel")
    
    with st.form("create_parcel"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Sender Information**")
            sender_name = st.text_input("Sender Name", key="sender_name")
            sender_phone = st.text_input("Sender Phone", key="sender_phone")
            sender_country_code = st.selectbox("Sender Country", ["+1", "+44", "+91", "+86", "+81"], key="sender_country")
            sender_location = st.text_input("Sender Location", key="sender_location")
            
        with col2:
            st.markdown("**Receiver Information**")
            receiver_name = st.text_input("Receiver Name", key="receiver_name")
            receiver_phone = st.text_input("Receiver Phone", key="receiver_phone")
            receiver_country_code = st.selectbox("Receiver Country", ["+1", "+44", "+91", "+86", "+81"], key="receiver_country")
            receiver_location = st.text_input("Receiver Location", key="receiver_location")
        
        st.markdown("**Parcel Details**")
        parcel_type = st.selectbox("Parcel Type", ["Document", "Package", "Fragile", "Electronics", "Clothing", "Other"], key="parcel_type")
        
        col3, col4 = st.columns(2)
        with col3:
            st.markdown("**Declared Value**")
            value_amount = st.number_input("Value Amount", min_value=0.0, step=0.01, key="value_amount")
            value_currency = st.selectbox("Value Currency", ["USD", "EUR", "GBP", "INR", "CNY"], key="value_currency")
        
        with col4:
            st.markdown("**Amount Paid**")
            amount_paid = st.number_input("Amount Paid", min_value=0.0, step=0.01, key="amount_paid")
            amount_currency = st.selectbox("Paid Currency", ["USD", "EUR", "GBP", "INR", "CNY"], key="amount_currency")
        
        special_instructions = st.text_area("Special Instructions", key="special_instructions")
        
        submitted = st.form_submit_button("Create Parcel", type="primary")
        
        if submitted:
            if not all([sender_name, sender_phone, receiver_name, receiver_phone, parcel_type, value_amount, amount_paid]):
                st.error("Please fill in all required fields")
                return
            
            try:
                payload = {
                    "sender_name": sender_name,
                    "sender_phone": f"{sender_country_code}{sender_phone}",
                    "sender_country_code": sender_country_code,
                    "receiver_name": receiver_name,
                    "receiver_phone": f"{receiver_country_code}{receiver_phone}",
                    "receiver_country_code": receiver_country_code,
                    "sender_location": sender_location,
                    "receiver_location": receiver_location,
                    "parcel_type": parcel_type,
                    "value": {
                        "amount": value_amount,
                        "currency": value_currency
                    },
                    "amount_paid": {
                        "amount": amount_paid,
                        "currency": amount_currency
                    },
                    "special_instructions": special_instructions
                }
                
                result = api_client.post("/parcels", payload, token=st.session_state.token)
                st.success(f"✅ Parcel created successfully! ID: {result['id']}")
                        st.rerun()
                
                    except Exception as e:
                st.error(f"❌ Failed to create parcel: {str(e)}")

def assign_rider_form(parcel_id: str, riders: list):
    """Form to assign a rider to a parcel"""
    st.subheader("🚚 Assign Rider")
    
    # Check if parcel already has an assignment
    try:
        assignments = api_client.get("/dispatch", token=st.session_state.token) or []
        current_assignment = next((a for a in assignments if a.get("parcel_id") == parcel_id), None)
        
        if current_assignment:
            st.info(f"Parcel is currently assigned to: {current_assignment.get('rider_name', 'Unknown Rider')}")
            if st.button("Reassign Rider"):
                st.session_state.reassigning = True
                st.rerun()
                        else:
            st.info("No rider currently assigned to this parcel")
                            
                    except Exception as e:
        st.warning(f"Could not check current assignment: {str(e)}")
    
    if st.button("Assign New Rider") or st.session_state.get("reassigning", False):
        with st.form("assign_rider"):
            rider_options = {r["id"]: f"{r['full_name']} ({r['phone']})" for r in riders if r.get("is_active", True)}
            
            if not rider_options:
                st.error("No active riders available")
                return
                
            selected_rider = st.selectbox("Select Rider", options=list(rider_options.keys()), format_func=lambda x: rider_options[x])
            
            if st.form_submit_button("Assign Rider"):
                try:
                    payload = {"rider_id": selected_rider}
                    result = api_client.post(f"/dispatch/{parcel_id}/assign", payload, token=st.session_state.token)
                    st.success(f"✅ Rider assigned successfully!")
                    st.session_state.reassigning = False
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to assign rider: {str(e)}")

def update_parcel_status_form(parcel: Dict[str, Any]):
    """Form to update parcel status"""
    st.subheader("📊 Update Parcel Status")
    
    current_status = parcel.get("current_status", "RECEIVED")
    st.info(f"Current Status: {get_parcel_status_color(current_status)} {current_status}")
    
    # Define allowed status transitions
    status_transitions = {
        "RECEIVED": ["PROCESSING", "CANCELLED"],
        "PROCESSING": ["IN_TRANSIT", "CANCELLED"],
        "IN_TRANSIT": ["ARRIVED_AT_HUB", "CANCELLED"],
        "ARRIVED_AT_HUB": ["OUT_FOR_DELIVERY", "CANCELLED"],
        "OUT_FOR_DELIVERY": ["DELIVERY_ATTEMPTED", "DELIVERED", "RETURNED"],
        "DELIVERY_ATTEMPTED": ["OUT_FOR_DELIVERY", "DELIVERED", "RETURNED"],
        "DELIVERED": [],
        "RETURNED": [],
        "CANCELLED": []
    }
    
    allowed_statuses = status_transitions.get(current_status, [])
    
    if not allowed_statuses:
        st.warning("This parcel has reached a final status and cannot be updated further.")
        return
    
    with st.form("update_status"):
        new_status = st.selectbox("New Status", allowed_statuses, key="new_status")
        location = st.text_input("Location", value="Main Hub", key="location")
        notes = st.text_area("Notes", key="notes")
        
        if st.form_submit_button("Update Status"):
                            try:
                                payload = {
                                    "status": new_status,
                                    "location": location,
                    "notes": notes or f"Status updated to {new_status}"
                }
                
                result = api_client.post(f"/parcels/{parcel['id']}/track", payload, token=st.session_state.token)
                st.success(f"✅ Status updated to {new_status} successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Failed to update status: {str(e)}")

def dispatch_parcel_form(parcel: Dict[str, Any]):
    """Form to dispatch a parcel"""
    st.subheader("📤 Dispatch Parcel")
    
    if parcel.get("dispatched"):
        st.info("✅ This parcel has already been dispatched")
        return
    
    # Check if parcel has a rider assigned
    try:
        assignments = api_client.get("/dispatch", token=st.session_state.token) or []
        has_rider = any(a.get("parcel_id") == parcel["id"] for a in assignments)
        
        if not has_rider:
            st.warning("⚠️ Please assign a rider before dispatching")
            return
            
    except Exception as e:
        st.warning(f"Could not check rider assignment: {str(e)}")
        return
    
    if st.button("Dispatch Parcel", type="primary"):
        try:
            result = api_client.post(f"/dispatch/{parcel['id']}/dispatch", token=st.session_state.token)
            st.success("✅ Parcel dispatched successfully! OTP has been sent to receiver.")
                                st.rerun()
                            except Exception as e:
            st.error(f"❌ Failed to dispatch parcel: {str(e)}")

def view_tracking_history(parcel_id: str):
    """Display tracking history for a parcel"""
    st.subheader("📍 Tracking History")
    
    try:
        tracking_history = api_client.get(f"/parcels/{parcel_id}/track", token=st.session_state.token) or []
        
        if tracking_history:
            # Create timeline
            for i, event in enumerate(reversed(tracking_history)):  # Show latest first
                status = event.get("status", "Unknown")
                location = event.get("location", "Unknown")
                notes = event.get("notes", "No notes")
                created_at = event.get("created_at", "Unknown")
                
                # Format timestamp
                try:
                    if isinstance(created_at, str):
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        formatted_time = str(created_at)
                except:
                    formatted_time = str(created_at)
                
                with st.expander(f"{get_parcel_status_color(status)} {status} - {formatted_time}", expanded=(i == 0)):
                    st.write(f"**Location:** {location}")
                    st.write(f"**Notes:** {notes}")
                    if event.get("updated_by_staff_id"):
                        st.write(f"**Updated by:** Staff ID {event['updated_by_staff_id']}")
        else:
            st.info("No tracking history available for this parcel.")
            
    except Exception as e:
        st.error(f"Failed to fetch tracking history: {str(e)}")

def render_parcel_management(token: str):
    st.title("📦 Parcel Management")
    
    # Initialize session state
    if "reassigning" not in st.session_state:
        st.session_state.reassigning = False
    
    try:
        # Fetch data
        parcels = api_client.get("/parcels", token) or []
        riders = api_client.get("/riders", token) or []
        
        # Create tabs for different functionalities
        tab1, tab2, tab3, tab4 = st.tabs(["📋 All Parcels", "➕ Create Parcel", "🚚 Manage Parcels", "📊 Analytics"])
        
        with tab1:
            st.subheader("All Parcels")
            
            if parcels:
                # Prepare data for display
                display_data = []
                for parcel in parcels:
                    # Get rider assignment info
                    rider_name = "Unassigned"
                    try:
                        assignments = api_client.get("/dispatch", token=token) or []
                        assignment = next((a for a in assignments if a.get("parcel_id") == parcel["id"]), None)
                        if assignment:
                            rider = next((r for r in riders if r["id"] == assignment.get("rider_id")), None)
                            if rider:
                                rider_name = rider["full_name"]
                    except:
                        pass
                    
                    display_data.append({
                        "ID": parcel["id"][:8] + "...",
                        "Sender": parcel["sender_name"],
                        "Receiver": parcel["receiver_name"],
                        "Type": parcel["parcel_type"],
                        "Status": f"{get_parcel_status_color(parcel['current_status'])} {parcel['current_status']}",
                        "Value": format_currency(parcel["value_amount"], parcel["value_currency"]),
                        "Paid": format_currency(parcel["amount_paid_amount"], parcel["amount_paid_currency"]),
                        "Rider": rider_name,
                        "Received": parcel["received_at"][:10] if parcel.get("received_at") else "N/A",
                        "Dispatched": "✅" if parcel.get("dispatched") else "❌",
                        "Delivered": "✅" if parcel.get("delivered") else "❌"
                    })
                
                df = pd.DataFrame(display_data)
                st.dataframe(df, use_container_width=True)
                
                # Search and filter
                st.subheader("🔍 Search & Filter")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    search_term = st.text_input("Search by ID, Name, or Phone", key="search")
                
                with col2:
                    status_filter = st.selectbox("Filter by Status", ["All"] + list(set(p["current_status"] for p in parcels)), key="status_filter")
                
                with col3:
                    rider_filter = st.selectbox("Filter by Rider", ["All"] + list(set(d["Rider"] for d in display_data)), key="rider_filter")
                
                # Apply filters
                if search_term or status_filter != "All" or rider_filter != "All":
                    filtered_df = df.copy()
                    
                    if search_term:
                        mask = (
                            filtered_df["ID"].str.contains(search_term, case=False, na=False) |
                            filtered_df["Sender"].str.contains(search_term, case=False, na=False) |
                            filtered_df["Receiver"].str.contains(search_term, case=False, na=False)
                        )
                        filtered_df = filtered_df[mask]
                    
                    if status_filter != "All":
                        filtered_df = filtered_df[filtered_df["Status"].str.contains(status_filter, na=False)]
                    
                    if rider_filter != "All":
                        filtered_df = filtered_df[filtered_df["Rider"] == rider_filter]
                    
                    st.subheader("Filtered Results")
                    st.dataframe(filtered_df, use_container_width=True)
        
        else:
            st.info("No parcels found.")
        
        with tab2:
            create_parcel_form()
        
        with tab3:
            st.subheader("Manage Individual Parcels")
            
            if parcels:
                # Select parcel to manage
                parcel_options = {p["id"]: f"{p['id'][:8]}... - {p['sender_name']} → {p['receiver_name']} ({p['current_status']})" for p in parcels}
                selected_parcel_id = st.selectbox("Select Parcel to Manage", options=list(parcel_options.keys()), format_func=lambda x: parcel_options[x])
                
                if selected_parcel_id:
                    selected_parcel = next((p for p in parcels if p["id"] == selected_parcel_id), None)
                    
                    if selected_parcel:
                        # Display parcel details
                        st.markdown("---")
                        st.subheader("📋 Parcel Details")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**ID:** {selected_parcel['id']}")
                            st.write(f"**Sender:** {selected_parcel['sender_name']} ({selected_parcel['sender_phone']})")
                            st.write(f"**Receiver:** {selected_parcel['receiver_name']} ({selected_parcel['receiver_phone']})")
                            st.write(f"**Type:** {selected_parcel['parcel_type']}")
                            st.write(f"**Status:** {get_parcel_status_color(selected_parcel['current_status'])} {selected_parcel['current_status']}")
                        
                        with col2:
                            st.write(f"**Value:** {format_currency(selected_parcel['value_amount'], selected_parcel['value_currency'])}")
                            st.write(f"**Paid:** {format_currency(selected_parcel['amount_paid_amount'], selected_parcel['amount_paid_currency'])}")
                            st.write(f"**Received:** {selected_parcel['received_at'][:19] if selected_parcel.get('received_at') else 'N/A'}")
                            st.write(f"**Dispatched:** {'✅' if selected_parcel.get('dispatched') else '❌'}")
                            st.write(f"**Delivered:** {'✅' if selected_parcel.get('delivered') else '❌'}")
                        
                        if selected_parcel.get("special_instructions"):
                            st.write(f"**Special Instructions:** {selected_parcel['special_instructions']}")
                        
                        # Management actions
                        st.markdown("---")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            assign_rider_form(selected_parcel["id"], riders)
                        
                        with col2:
                            update_parcel_status_form(selected_parcel)
                        
                        with col3:
                            dispatch_parcel_form(selected_parcel)
                        
                        # Tracking history
                        st.markdown("---")
                        view_tracking_history(selected_parcel["id"])
                        
            else:
                st.info("No parcels available to manage.")
        
        with tab4:
            st.subheader("📊 Parcel Analytics")
            
            if parcels:
                col1, col2, col3, col4 = st.columns(4)
                
                # Total parcels
                with col1:
                    st.metric("Total Parcels", len(parcels))
                
                # Status breakdown
                with col2:
                    status_counts = {}
                    for parcel in parcels:
                        status = parcel.get("current_status", "Unknown")
                        status_counts[status] = status_counts.get(status, 0) + 1
                    
                    most_common_status = max(status_counts.items(), key=lambda x: x[1]) if status_counts else ("None", 0)
                    st.metric("Most Common Status", f"{most_common_status[0]} ({most_common_status[1]})")
                
                # Dispatched vs not dispatched
                with col3:
                    dispatched_count = sum(1 for p in parcels if p.get("dispatched"))
                    st.metric("Dispatched", f"{dispatched_count}/{len(parcels)}")
                
                # Delivered vs not delivered
                with col4:
                    delivered_count = sum(1 for p in parcels if p.get("delivered"))
                    st.metric("Delivered", f"{delivered_count}/{len(parcels)}")
                
                # Status distribution chart
                st.subheader("Status Distribution")
                status_df = pd.DataFrame(list(status_counts.items()), columns=["Status", "Count"])
                st.bar_chart(status_df.set_index("Status"))
                
                # Recent activity
                st.subheader("Recent Activity")
                recent_parcels = sorted(parcels, key=lambda x: x.get("received_at", ""), reverse=True)[:10]
                recent_data = []
                
                for parcel in recent_parcels:
                    recent_data.append({
                        "ID": parcel["id"][:8] + "...",
                        "Sender": parcel["sender_name"],
                        "Status": parcel["current_status"],
                        "Received": parcel["received_at"][:10] if parcel.get("received_at") else "N/A"
                    })
                
                if recent_data:
                    st.dataframe(pd.DataFrame(recent_data), use_container_width=True)
                
            else:
                st.info("No data available for analytics.")
            
    except Exception as e:
        st.error(f"Error loading parcels: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    demo_token = st.secrets.get("API_TOKEN", "") if hasattr(st, "secrets") else ""
    render_parcel_management(demo_token)