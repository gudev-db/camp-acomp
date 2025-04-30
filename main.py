import streamlit as st
import pandas as pd
import numpy as np
from google.generativeai import GenerativeModel
import os

# Configuration
st.set_page_config(layout="wide", page_title="Campaign Performance Dashboard")

# Gemini API setup
gemini_api_key = os.getenv("GEM_API_KEY")
model = GenerativeModel('gemini-pro') if gemini_api_key else None

def load_data(uploaded_file):
    """Load and preprocess the CSV file"""
    try:
        df = pd.read_csv(uploaded_file, skiprows=2)  # Skip header rows
        df = df.dropna(how='all')  # Remove empty rows
        
        # Clean numeric columns
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.replace(',', '').str.replace('%', '')
                try:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except:
                    pass
        
        return df
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

def calculate_metrics(df):
    """Calculate averages and identify campaigns above/below average"""
    metrics = {}
    
    # Identify numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Calculate averages
    for col in numeric_cols:
        if col in ['Campaign ID']:  # Skip ID columns
            continue
            
        avg = df[col].mean()
        metrics[col] = {
            'average': avg,
            'above_avg': df[df[col] > avg]['Campaign'].tolist(),
            'below_avg': df[df[col] < avg]['Campaign'].tolist()
        }
    
    return metrics

def generate_llm_report(df, metrics):
    """Generate a detailed report using LLM"""
    if not model:
        return "Gemini API key not configured. Report generation disabled."
    
    # Prepare data summary for LLM
    summary = f"""
    Campaign Performance Report Summary:
    - Total campaigns: {len(df)}
    - Active campaigns: {len(df[df['Campaign status'] == 'Active'])}
    - Paused campaigns: {len(df[df['Campaign status'] == 'Paused'])}
    
    Key Metrics Averages:
    """
    
    for col, data in metrics.items():
        summary += f"- {col}: {data['average']:.2f}\n"
    
    prompt = f"""
    You are a digital marketing analytics expert. Analyze this campaign performance data and generate a detailed report in Portuguese.
    
    Data Summary:
    {summary}
    
    Report Requirements:
    1. Start with an executive summary highlighting overall performance
    2. Create sections for each major metric (CPV, CPM, CTR, etc.)
    3. For each metric:
       - Explain what it measures
       - Analyze the average performance
       - Highlight top 3 performing campaigns
       - Highlight bottom 3 performing campaigns
       - Provide recommendations for improvement
    4. End with overall conclusions and strategic recommendations
    
    Format the report professionally with markdown headings.
    """
    
    response = model.generate_content(prompt)
    return response.text

def main():
    st.title("📊 Campaign Performance Analytics Dashboard")
    
    # File upload
    uploaded_file = st.file_uploader("Upload Campaign CSV Report", type=["csv"])
    
    if uploaded_file:
        df = load_data(uploaded_file)
        
        if df is not None:
            st.success("Data loaded successfully!")
            
            # Calculate metrics
            metrics = calculate_metrics(df)
            
            # Display data
            st.subheader("Campaign Data Preview")
            st.dataframe(df.head(), use_container_width=True)
            
            # Metrics tabs
            tab1, tab2, tab3 = st.tabs(["📈 Key Metrics", "🔍 Campaign Analysis", "📝 AI Report"])
            
            with tab1:
                st.subheader("Key Performance Metrics")
                
                # Select metric to visualize
                metric_cols = [col for col in metrics.keys() if col not in ['Campaign ID']]
                selected_metric = st.selectbox("Select metric to analyze", metric_cols)
                
                if selected_metric:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric(
                            label=f"Average {selected_metric}",
                            value=f"{metrics[selected_metric]['average']:.2f}"
                        )
                        
                        st.write("**Top Performing Campaigns (Above Average)**")
                        st.dataframe(
                            df[df['Campaign'].isin(metrics[selected_metric]['above_avg'])][['Campaign', selected_metric]].sort_values(selected_metric, ascending=False),
                            height=300
                        )
                    
                    with col2:
                        st.write("**Below Average**")
                        st.dataframe(
                            df[df['Campaign'].isin(metrics[selected_metric]['below_avg'])][['Campaign', selected_metric]].sort_values(selected_metric),
                            height=300
                        )
                    
                    # Metric trend visualization
                    st.subheader("Performance Distribution")
                    st.bar_chart(df[selected_metric])
            
            with tab2:
                st.subheader("Campaign Performance Analysis")
                
                # Filter options
                campaign_type = st.multiselect(
                    "Filter by Campaign Type",
                    options=df['Campaign type'].unique(),
                    default=df['Campaign type'].unique()
                )
                
                status_filter = st.multiselect(
                    "Filter by Status",
                    options=df['Campaign status'].unique(),
                    default=df['Campaign status'].unique()
                )
                
                # Apply filters
                filtered_df = df[
                    (df['Campaign type'].isin(campaign_type)) &
                    (df['Campaign status'].isin(status_filter))
                ]
                
                # Display filtered data
                st.dataframe(filtered_df, use_container_width=True)
                
                # Performance comparison
                st.subheader("Performance Comparison")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Highest Performing Campaigns**")
                    top_campaigns = filtered_df.nlargest(5, 'Interactions')[['Campaign', 'Interactions', 'Interaction rate']]
                    st.dataframe(top_campaigns)
                
                with col2:
                    st.write("**Lowest Performing Campaigns**")
                    bottom_campaigns = filtered_df.nsmallest(5, 'Interactions')[['Campaign', 'Interactions', 'Interaction rate']]
                    st.dataframe(bottom_campaigns)
            
            with tab3:
                st.subheader("AI-Powered Performance Report")
                
                if st.button("Generate Report"):
                    with st.spinner("Generating detailed report..."):
                        report = generate_llm_report(df, metrics)
                        st.markdown(report)
                        
                        # Download option
                        st.download_button(
                            label="Download Report",
                            data=report,
                            file_name="campaign_performance_report.md",
                            mime="text/markdown"
                        )

if __name__ == "__main__":
    main()
