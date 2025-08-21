import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add dashboard root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import api_client


def render_analytics(token: str):
    """Render the analytics page with detailed metrics"""
    st.title("Analytics & Performance")
    
    try:
        # Fetch data
        parcels = api_client.get("/parcels", token)
        staff_list = api_client.get("/staff", token)
        riders = api_client.get("/riders", token)
        
        if not parcels:
            st.info("No parcel data available for analytics.")
            return
        
        df = pd.DataFrame(parcels)
        df['received_at'] = pd.to_datetime(df['received_at'])
        df['dispatched_at'] = pd.to_datetime(df['dispatched_at'])
        df['delivered_at'] = pd.to_datetime(df['delivered_at'])
        
        # Delivery Performance Analysis
        st.header("Delivery Performance")
        
        # Success rate by day
        col1, col2 = st.columns(2)
        with col1:
            daily_success = df.groupby(df['received_at'].dt.date).agg({
                'delivery_outcome': lambda x: (x == 'SUCCESS').sum(),
                'id': 'count'
            }).reset_index()
            daily_success.columns = ['date', 'successful', 'total']
            daily_success['success_rate'] = (daily_success['successful'] / daily_success['total'] * 100)
            
            fig = px.line(daily_success, x='date', y='success_rate', 
                         title='Daily Delivery Success Rate (%)')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Outcome distribution
            outcome_counts = df['delivery_outcome'].value_counts()
            fig = px.pie(values=outcome_counts.values, names=outcome_counts.index, 
                        title='Overall Delivery Outcomes')
            st.plotly_chart(fig, use_container_width=True)
        
        # Staff Performance
        st.header("Staff Performance Analysis")
        
        if staff_list:
            staff_df = pd.DataFrame(staff_list)
            
            # Parcels handled per staff member
            staff_performance = df.groupby('received_by_id').size().reset_index(name='parcels_handled')
            staff_performance = staff_performance.merge(
                staff_df[['id', 'full_name', 'role']], 
                left_on='received_by_id', 
                right_on='id', 
                how='left'
            )
            
            if not staff_performance.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.bar(staff_performance, x='full_name', y='parcels_handled', 
                                color='role', title='Parcels Handled by Staff')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Role performance
                    role_performance = staff_performance.groupby('role')['parcels_handled'].mean().reset_index()
                    fig = px.bar(role_performance, x='role', y='parcels_handled', 
                                title='Average Parcels per Role')
                    st.plotly_chart(fig, use_container_width=True)
        
        # Time Analysis
        st.header("Time Analysis")
        
        # Delivery time analysis
        delivery_df = df[df['delivered'] == True].copy()
        if not delivery_df.empty:
            delivery_df['delivery_time'] = (
                delivery_df['delivered_at'] - delivery_df['received_at']
            ).dt.total_seconds() / 3600  # Convert to hours
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.histogram(delivery_df, x='delivery_time', 
                                 title='Delivery Time Distribution (Hours)',
                                 nbins=20)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                avg_delivery_time = delivery_df['delivery_time'].mean()
                st.metric("Average Delivery Time", f"{avg_delivery_time:.1f} hours")
                
                # Fastest and slowest deliveries
                fastest = delivery_df.loc[delivery_df['delivery_time'].idxmin()]
                slowest = delivery_df.loc[delivery_df['delivery_time'].idxmax()]
                
                st.write("**Fastest Delivery:**")
                st.write(f"• {fastest['sender_name']} → {fastest['receiver_name']}")
                st.write(f"• Time: {fastest['delivery_time']:.1f} hours")
                
                st.write("**Slowest Delivery:**")
                st.write(f"• {slowest['sender_name']} → {slowest['receiver_name']}")
                st.write(f"• Time: {slowest['delivery_time']:.1f} hours")
        
        # Financial Analysis
        st.header("Financial Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Value distribution
            fig = px.histogram(df, x='value_amount', title='Parcel Value Distribution',
                             nbins=20)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Payment vs Value
            df['profit_margin'] = df['amount_paid_amount'] - df['value_amount']
            fig = px.scatter(df, x='value_amount', y='amount_paid_amount', 
                           title='Payment vs Value',
                           color='delivery_outcome')
            st.plotly_chart(fig, use_container_width=True)
        
        # Summary metrics
        st.header("Summary Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Revenue", f"${df['amount_paid_amount'].sum():,.2f}")
        col2.metric("Total Parcel Value", f"${df['value_amount'].sum():,.2f}")
        col3.metric("Average Parcel Value", f"${df['value_amount'].mean():,.2f}")
        col4.metric("Success Rate", f"{(df['delivery_outcome'] == 'SUCCESS').mean() * 100:.1f}%")
        
    except Exception as e:
        st.error(f"Error loading analytics data: {str(e)}")
        st.info("Please check your connection and try again.")
