import streamlit as st
import pandas as pd
import numpy as np
from io import StringIO
from google import genai
import os

# Set page config
st.set_page_config(page_title="Campaign Performance Dashboard", layout="wide")

# Initialize Gemini API
gemini_api_key = os.getenv("GEM_API_KEY")
if gemini_api_key:
    client = genai.Client(api_key=gemini_api_key)
else:
    st.warning("Gemini API key not found. LLM features will be disabled.")

# Function to clean and preprocess data
def preprocess_data(df):
    # Convert numeric columns with commas to floats
    numeric_cols = ['Budget', 'Avg. CPV', 'Avg. CPV (Converted currency)', 
                   'Avg. CPM', 'Avg. CPM (Converted currency)', 'Avg. cost',
                   'Avg. cost (Converted currency)', 'Cost', 'Cost (Converted currency)',
                   'Avg. CPC', 'Avg. CPC (Converted currency)', 'Cost / conv.',
                   'Cost (Converted currency) / conv.']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].replace('--', np.nan)
            df[col] = df[col].str.replace(',', '').astype(float)
    
    # Clean other columns
    if 'Interactions' in df.columns:
        df['Interactions'] = df['Interactions'].str.replace(',', '').astype(float)
    if 'Impr.' in df.columns:
        df['Impr.'] = df['Impr.'].str.replace(',', '').astype(float)
    if 'Clicks' in df.columns:
        df['Clicks'] = df['Clicks'].str.replace(',', '').astype(float)
    
    return df

# Function to generate performance metrics
def generate_metrics(df):
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    metrics = df[numeric_cols].describe().loc[['mean', '50%', 'min', 'max']]
    return metrics

# Function to identify campaigns above/below average
def get_campaigns_by_metric(df, metric, above=True):
    mean_value = df[metric].mean()
    if above:
        return df[df[metric] > mean_value][['Campaign', metric]]
    else:
        return df[df[metric] <= mean_value][['Campaign', metric]]

# Function to generate LLM insights
def generate_llm_insights(df, metric):
    if not gemini_api_key:
        return "LLM features disabled - API key not configured"
    
    prompt = f"""
    Analyze the campaign performance data for the metric: {metric}. 
    Provide detailed insights in Portuguese about what the numbers mean, 
    which campaigns are performing well or poorly, and recommendations for optimization.
    Focus on practical actions and be specific.
    
    Data Summary:
    Mean: {df[metric].mean():.2f}
    Median: {df[metric].median():.2f}
    Min: {df[metric].min():.2f}
    Max: {df[metric].max():.2f}
    
    Top performing campaigns:
    {df.nlargest(3, metric)[['Campaign', metric]].to_string()}
    
    Worst performing campaigns:
    {df.nsmallest(3, metric)[['Campaign', metric]].to_string()}
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[prompt]
        )
        return response.text
    except Exception as e:
        return f"Error generating insights: {str(e)}"

# Main app
def main():
    st.title("📊 Campaign Performance Dashboard")
    
    # File upload
    uploaded_file = st.file_uploader("Upload your campaign CSV file", type=["csv"])
    
    if uploaded_file is not None:
        # Read and preprocess data
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        df = pd.read_csv(stringio, skiprows=2)  # Skip header rows
        df = preprocess_data(df)
        
        # Display raw data
        st.subheader("Raw Data Preview")
        st.dataframe(df.head())
        
        # Generate metrics
        st.subheader("📈 Performance Metrics")
        metrics = generate_metrics(df)
        st.dataframe(metrics.style.format("{:.2f}"))
        
        # Campaign analysis
        st.subheader("🔍 Campaign Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### Top Performing Campaigns")
            metric = st.selectbox("Select metric to analyze:", 
                                df.select_dtypes(include=[np.number]).columns.tolist())
            
            top_campaigns = df.nlargest(5, metric)[['Campaign', metric]]
            st.dataframe(top_campaigns)
            
            st.write("### Campaigns Above Average")
            above_avg = get_campaigns_by_metric(df, metric, above=True)
            st.dataframe(above_avg)
        
        with col2:
            st.write("### Worst Performing Campaigns")
            bottom_campaigns = df.nsmallest(5, metric)[['Campaign', metric]]
            st.dataframe(bottom_campaigns)
            
            st.write("### Campaigns Below Average")
            below_avg = get_campaigns_by_metric(df, metric, above=False)
            st.dataframe(below_avg)
        
        # Visualization
        st.subheader("📊 Visualization")
        
        chart_type = st.selectbox("Select chart type:", 
                                ["Bar Chart", "Line Chart", "Scatter Plot"])
        
        if chart_type == "Bar Chart":
            st.bar_chart(df.set_index('Campaign')[metric].nlargest(10))
        elif chart_type == "Line Chart":
            st.line_chart(df.set_index('Campaign')[metric].nlargest(10))
        else:
            if 'Cost' in df.columns and 'Clicks' in df.columns:
                st.scatter_chart(df, x='Cost', y='Clicks', color='Campaign')
        
        # LLM Insights
        st.subheader("🤖 AI-Powered Insights")
        
        if st.button("Generate Detailed Report"):
            with st.spinner("Generating insights..."):
                metrics_to_analyze = ['Avg. CPC', 'Avg. CPM', 'Cost', 'Interaction rate', 'Impr.']
                
                for metric in metrics_to_analyze:
                    if metric in df.columns:
                        with st.expander(f"Insights for {metric}"):
                            insights = generate_llm_insights(df, metric)
                            st.write(insights)

if __name__ == "__main__":
    main()