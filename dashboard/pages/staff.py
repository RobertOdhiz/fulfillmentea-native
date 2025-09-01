import streamlit as st
import pandas as pd
import sys
import os

# Add dashboard root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import api_client


def render_staff(token: str):
    """Render the staff management page"""
    st.title("👥 Staff Management")
    
    try:
        # Fetch staff
        staff_list = api_client.get("/staff", token)
        
        # Display staff table
        st.subheader("Current Staff")
        if staff_list:
            df = pd.DataFrame(staff_list)
            st.dataframe(df[['full_name', 'phone', 'email', 'role', 'is_active']], 
                        use_container_width=True)
        else:
            st.info("No staff found.")
        
        # Add new staff
        st.subheader("Add New Staff Member")
        with st.form("add_staff"):
            col1, col2 = st.columns(2)
            with col1:
                full_name = st.text_input("Full Name")
                phone = st.text_input("Phone Number")
                email = st.text_input("Email (optional)")
            with col2:
                role = st.selectbox("Role", [
                    "SUPER_ADMIN", "ADMIN", "MANAGER", "SALES_AGENT", 
                    "RECEIVING", "DISPATCHER", "DELIVERY"
                ])
                password = st.text_input("Password", type="password")
            
            submitted = st.form_submit_button("Add Staff Member", type="primary")
            
            if submitted:
                try:
                    new_staff = api_client.post("/auth/bootstrap", {
                        "full_name": full_name,
                        "phone": phone,
                        "email": email if email else None,
                        "role": role,
                        "password": password
                    }, token)
                    st.success(f"Staff member {full_name} added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to add staff member: {str(e)}")
        
        # Edit/Delete staff
        if staff_list:
            st.subheader("Edit/Delete Staff")
            selected_staff = st.selectbox("Select Staff to Edit", 
                                        options=staff_list, 
                                        format_func=lambda x: f"{x['full_name']} ({x['role']})")
            
            if selected_staff:
                with st.form("edit_staff"):
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_name = st.text_input("Full Name", value=selected_staff['full_name'])
                        edit_phone = st.text_input("Phone", value=selected_staff['phone'])
                        edit_email = st.text_input("Email", value=selected_staff.get('email', ''))
                    with col2:
                        edit_role = st.selectbox("Role", [
                            "SUPER_ADMIN", "ADMIN", "MANAGER", "SALES_AGENT", 
                            "RECEIVING", "DISPATCHER", "DELIVERY"
                        ], index=[
                            "SUPER_ADMIN", "ADMIN", "MANAGER", "SALES_AGENT", 
                            "RECEIVING", "DISPATCHER", "DELIVERY"
                        ].index(selected_staff['role']))
                        edit_password = st.text_input("New Password (leave blank to keep current)", type="password")
                        edit_is_active = st.checkbox("Active", value=selected_staff['is_active'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Update Staff"):
                            try:
                                update_data = {
                                    "full_name": edit_name,
                                    "phone": edit_phone,
                                    "email": edit_email if edit_email else None,
                                    "role": edit_role,
                                    "is_active": edit_is_active
                                }
                                if edit_password:
                                    update_data["password"] = edit_password
                                
                                updated_staff = api_client.put(f"/staff/{selected_staff['id']}", update_data, token)
                                st.success(f"Staff member {edit_name} updated successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to update staff member: {str(e)}")
                    
                    with col2:
                        if st.form_submit_button("Delete Staff", type="secondary"):
                            try:
                                result = api_client.delete(f"/staff/{selected_staff['id']}", token)
                                st.success(result['message'])
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to delete staff member: {str(e)}")
        
        # Staff performance metrics
        if staff_list:
            st.subheader("Staff Performance")
            
            # Role distribution
            role_counts = df['role'].value_counts()
            st.write("**Role Distribution:**")
            for role, count in role_counts.items():
                st.write(f"• {role}: {count}")
            
            # Active vs Inactive
            active_count = df['is_active'].sum()
            inactive_count = len(df) - active_count
            col1, col2 = st.columns(2)
            col1.metric("Active Staff", active_count)
            col2.metric("Inactive Staff", inactive_count)
            
            # Staff activity (if parcels data available)
            try:
                parcels = api_client.get("/parcels", token)
                if parcels:
                    st.subheader("Staff Activity")
                    parcel_df = pd.DataFrame(parcels)
                    staff_activity = parcel_df.groupby('received_by_id').size().reset_index(name='parcels_handled')
                    
                    # Merge with staff info
                    activity_df = staff_activity.merge(
                        df[['id', 'full_name', 'role']], 
                        left_on='received_by_id', 
                        right_on='id', 
                        how='left'
                    )
                    
                    if not activity_df.empty:
                        st.dataframe(activity_df[['full_name', 'role', 'parcels_handled']], 
                                   use_container_width=True)
                    else:
                        st.info("No parcel handling data available.")
            except:
                st.info("Parcel data not available for activity metrics.")
                            
    except Exception as e:
        st.error(f"Error loading staff data: {str(e)}")
        st.info("Please check your connection and try again.")
