import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def plot_metric_distribution(df, metric):
    """Plot distribution of a specific metric"""
    plt.figure(figsize=(10, 6))
    sns.histplot(df[metric], kde=True, bins=30)
    plt.title(f'Distribuição de {metric}')
    plt.xlabel(metric)
    plt.ylabel('Frequência')
    st.pyplot(plt)
    plt.close()

def plot_campaign_performance(df, metric, top_n=10):
    """Plot top performing campaigns"""
    plt.figure(figsize=(12, 6))
    top_campaigns = df.nlargest(top_n, metric)
    sns.barplot(x=metric, y='Campanha', data=top_campaigns)
    plt.title(f'Top {top_n} Campanhas por {metric}')
    plt.xlabel(metric)
    plt.ylabel('Campanha')
    st.pyplot(plt)
    plt.close()

def plot_correlation_heatmap(df, metrics):
    """Plot correlation heatmap for selected metrics"""
    plt.figure(figsize=(12, 8))
    corr_matrix = df[metrics].corr()
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
    plt.title('Matriz de Correlação entre Métricas')
    st.pyplot(plt)
    plt.close()
