import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# Add dashboard root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import api_client


def render_overview(token: str):
    """Render the overview dashboard with KPIs and charts"""
    st.title("Operations Overview")
    
    try:
        # Fetch data
        parcels = api_client.get("/parcels", token)
        
        # KPIs
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Parcels", len(parcels))
        col2.metric("Dispatched", sum(1 for p in parcels if p["dispatched"]))
        col3.metric("Delivered", sum(1 for p in parcels if p["delivered"]))
        col4.metric("Failures", sum(1 for p in parcels if p.get("delivery_outcome") == "FAILED"))
        col5.metric("Pending", sum(1 for p in parcels if p.get("delivery_outcome") == "PENDING"))
        
        if parcels:
            df = pd.DataFrame(parcels)
            df['received_at'] = pd.to_datetime(df['received_at'])
            
            # Time series chart
            st.subheader("📈 Parcels Received Per Day")
            timeseries = df.groupby(df['received_at'].dt.date).size().reset_index(name='count')
            fig1 = px.bar(timeseries, x='received_at', y='count', 
                         title='Daily Parcel Volume')
            st.plotly_chart(fig1, use_container_width=True)
            
            # Delivery outcomes pie chart
            st.subheader("🎯 Delivery Outcomes")
            outcome_counts = df['delivery_outcome'].value_counts().reset_index()
            outcome_counts.columns = ['outcome', 'count']
            fig2 = px.pie(outcome_counts, names='outcome', values='count', 
                         title='Delivery Success Rate')
            st.plotly_chart(fig2, use_container_width=True)
            
            # Status timeline
            st.subheader("📅 Recent Activity")
            recent = df.nlargest(10, 'received_at')[['id', 'sender_name', 'receiver_name', 'current_status', 'received_at']]
            st.dataframe(recent, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error loading overview data: {str(e)}")
        st.info("Please check your connection and try again.")
