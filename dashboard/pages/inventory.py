import streamlit as st
import pandas as pd
import sys
import os

# Add dashboard root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import api_client


def render_inventory(token: str):
    """Render the inventory management page"""
    st.title("Inventory Management")
    
    try:
        # Fetch inventory
        items = api_client.get("/inventory", token)
        
        # Display inventory table
        st.subheader("Current Inventory")
        if items:
            df = pd.DataFrame(items)
            st.dataframe(df[['name', 'sku', 'quantity', 'unit', 'is_active']], 
                        use_container_width=True)
        else:
            st.info("No inventory items found.")
        
        # Add new item
        st.subheader("Add New Item")
        with st.form("add_item"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Item Name")
                sku = st.text_input("SKU (optional)")
            with col2:
                quantity = st.number_input("Initial Quantity", value=0.0, min_value=0.0)
                unit = st.text_input("Unit", value="unit")
            
            submitted = st.form_submit_button("Add Item", type="primary")
            
            if submitted:
                try:
                    new_item = api_client.post("/inventory", {
                        "name": name,
                        "sku": sku if sku else None,
                        "quantity": quantity,
                        "unit": unit
                    }, token)
                    st.success(f"Item {name} added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to add item: {str(e)}")
        
        # Adjust quantities
        if items:
            st.subheader("Adjust Quantities")
            selected_item = st.selectbox("Select Item to Adjust", 
                                       options=items, 
                                       format_func=lambda x: f"{x['name']} ({x['sku'] or 'No SKU'})")
            
            if selected_item:
                with st.form("adjust_item"):
                    current_qty = selected_item['quantity']
                    st.info(f"Current quantity: {current_qty} {selected_item['unit']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        adjustment = st.number_input("Adjustment (+/-)", value=0.0)
                        st.caption(f"Positive to add, negative to subtract")
                    with col2:
                        new_total = current_qty + adjustment
                        st.metric("New Total", f"{new_total} {selected_item['unit']}")
                    
                    if st.form_submit_button("Apply Adjustment"):
                        try:
                            updated_item = api_client.post(f"/inventory/{selected_item['id']}/adjust", 
                                                         {"delta": adjustment}, token)
                            st.success(f"Quantity adjusted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to adjust quantity: {str(e)}")
            
            # Deactivate items
            st.subheader("Deactivate Items")
            deactivate_item = st.selectbox("Select Item to Deactivate", 
                                         options=items, 
                                         format_func=lambda x: f"{x['name']} ({x['sku'] or 'No SKU'})")
            
            if st.button("Deactivate Item", type="secondary"):
                try:
                    api_client.delete(f"/inventory/{deactivate_item['id']}", token)
                    st.success(f"Item {deactivate_item['name']} deactivated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to deactivate item: {str(e)}")
                            
    except Exception as e:
        st.error(f"Error loading inventory data: {str(e)}")
        st.info("Please check your connection and try again.")
