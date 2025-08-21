import streamlit as st
import pandas as pd
import sys
import os

# Add dashboard root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import api_client


def render_riders(token: str):
    """Render the riders management page"""
    st.title("Riders Management")
    
    try:
        # Fetch riders
        riders = api_client.get("/riders", token)
        
        # Display riders table
        st.subheader("Current Riders")
        if riders:
            df = pd.DataFrame(riders)
            st.dataframe(df[['full_name', 'phone', 'vehicle_details', 'is_active']], 
                        use_container_width=True)
        else:
            st.info("No riders found.")
        
        # Add new rider
        st.subheader("Add New Rider")
        with st.form("add_rider"):
            col1, col2 = st.columns(2)
            with col1:
                full_name = st.text_input("Full Name")
                phone = st.text_input("Phone Number")
            with col2:
                vehicle_details = st.text_input("Vehicle Details")
                is_active = st.checkbox("Active", value=True)
            
            submitted = st.form_submit_button("Add Rider", type="primary")
            
            if submitted:
                try:
                    new_rider = api_client.post("/riders", {
                        "full_name": full_name,
                        "phone": phone,
                        "vehicle_details": vehicle_details
                    }, token)
                    st.success(f"Rider {full_name} added successfully!")
                except Exception as e:
                    st.error(f"Failed to add rider: {str(e)}")
        
        # Edit/Delete riders
        if riders:
            st.subheader("Edit/Delete Riders")
            selected_rider = st.selectbox("Select Rider to Edit", 
                                        options=riders, 
                                        format_func=lambda x: f"{x['full_name']} ({x['phone']})")
            
            if selected_rider:
                with st.form("edit_rider"):
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_name = st.text_input("Full Name", value=selected_rider['full_name'])
                        edit_phone = st.text_input("Phone", value=selected_rider['phone'])
                    with col2:
                        edit_vehicle = st.text_input("Vehicle Details", value=selected_rider.get('vehicle_details', ''))
                        edit_active = st.checkbox("Active", value=selected_rider['is_active'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Update Rider"):
                            try:
                                updated_rider = api_client.put(f"/riders/{selected_rider['id']}", {
                                    "full_name": edit_name,
                                    "phone": edit_phone,
                                    "vehicle_details": edit_vehicle
                                }, token)
                                st.success(f"Rider {edit_name} updated successfully!")
        
                            except Exception as e:
                                st.error(f"Failed to update rider: {str(e)}")
                    
                    with col2:
                        if st.form_submit_button("Delete Rider", type="secondary"):
                            try:
                                result = api_client.delete(f"/riders/{selected_rider['id']}", token)
                                st.success(result['message'])
        
                            except Exception as e:
                                st.error(f"Failed to delete rider: {str(e)}")
                            
    except Exception as e:
        st.error(f"Error loading riders data: {str(e)}")
        st.info("Please check your connection and try again.")
