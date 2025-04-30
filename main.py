import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from google.generativeai import GenerativeModel
import os

# Configuração da página
st.set_page_config(
    layout="wide",
    page_title="Analytics de Campanhas",
    page_icon="📊"
)

# Título principal
st.title("📊 Analytics de Performance de Campanhas Digitais")

# Funções do aplicativo ==============================================

def carregar_dados(arquivo):
    """Carrega e prepara o arquivo CSV"""
    try:
        # Pula as 2 primeiras linhas de cabeçalho
        df = pd.read_csv(arquivo, skiprows=2)
        
        # Remove linhas completamente vazias
        df = df.dropna(how='all')
        
        # Limpa colunas numéricas
        for col in df.columns:
            if df[col].dtype == 'object':
                # Remove vírgulas, porcentagens e outros caracteres
                df[col] = df[col].astype(str).str.replace(',', '').str.replace('%', '').str.replace(' ', '')
                try:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except:
                    pass
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {str(e)}")
        return None

def calcular_metricas(df):
    """Calcula estatísticas básicas para todas as colunas numéricas"""
    metricas = {}
    colunas_numericas = df.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in colunas_numericas:
        if col in ['Campaign ID']:  # Ignora colunas de ID
            continue
            
        metricas[col] = {
            'média': df[col].mean(),
            'mediana': df[col].median(),
            'desvio_padrao': df[col].std(),
            'min': df[col].min(),
            'max': df[col].max(),
            'q1': df[col].quantile(0.25),
            'q3': df[col].quantile(0.75)
        }
    
    return metricas

def criar_boxplot(df, coluna):
    """Cria um boxplot para uma coluna numérica"""
    plt.figure(figsize=(8, 4))
    sns.boxplot(x=df[coluna])
    plt.title(f'Distribuição de {coluna}')
    plt.xlabel('Valor')
    st.pyplot(plt)
    plt.close()

def gerar_relatorio(df, metricas, colunas_selecionadas):
    """Gera um relatório analítico das campanhas"""
    relatorio = f"""
    # Relatório de Performance de Campanhas
    **Total de campanhas analisadas:** {len(df)}
    
    ## Resumo Estatístico
    """
    
    for col in colunas_selecionadas:
        if col in metricas:
            stats = metricas[col]
            relatorio += f"""
            ### {col}
            - Média: {stats['média']:,.2f}
            - Mediana: {stats['mediana']:,.2f} 
            - Intervalo: {stats['min']:,.2f} a {stats['max']:,.2f}
            - Desvio Padrão: {stats['desvio_padrao']:,.2f}
            
            """
    
    # Top performers
    relatorio += "## Campanhas com Melhor Performance\n"
    for col in colunas_selecionadas:
        if col in df.columns:
            top5 = df.nlargest(5, col)[['Campaign', col]]
            relatorio += f"**Maiores valores em {col}:**\n"
            for _, row in top5.iterrows():
                relatorio += f"- {row['Campaign']}: {row[col]:,.2f}\n"
            relatorio += "\n"
    
    # Bottom performers
    relatorio += "## Campanhas com Pior Performance\n"
    for col in colunas_selecionadas:
        if col in df.columns:
            bottom5 = df.nsmallest(5, col)[['Campaign', col]]
            relatorio += f"**Menores valores em {col}:**\n"
            for _, row in bottom5.iterrows():
                relatorio += f"- {row['Campaign']}: {row[col]:,.2f}\n"
            relatorio += "\n"
    
    return relatorio

# Interface do usuário ===============================================

# Upload do arquivo
arquivo = st.file_uploader(
    "📤 Carregue seu relatório de campanhas (formato CSV)",
    type=["csv"],
    help="O arquivo deve seguir o formato padrão dos relatórios do Google Ads"
)

if arquivo:
    df = carregar_dados(arquivo)
    
    if df is not None:
        st.success("✅ Dados carregados com sucesso!")
        
        # Calcula métricas
        metricas = calcular_metricas(df)
        colunas_numericas = [col for col in metricas.keys() if col != 'Campaign ID']
        
        # Sidebar com controles
        with st.sidebar:
            st.header("🔧 Configurações de Análise")
            
            # Seleção de métricas para o relatório
            metricas_relatorio = st.multiselect(
                "Selecione as métricas para incluir no relatório",
                options=colunas_numericas,
                default=colunas_numericas[:5]  # Primeiras 5 por padrão
            )
            
            # Filtros
            st.subheader("Filtros")
            tipo_campanha = st.multiselect(
                "Tipo de Campanha",
                options=df['Campaign type'].unique(),
                default=df['Campaign type'].unique()
            )
            
            status_campanha = st.multiselect(
                "Status da Campanha",
                options=df['Campaign status'].unique(),
                default=df['Campaign status'].unique()
            )
            
            # Opção para boxplots
            mostrar_boxplots = st.checkbox("Mostrar boxplots das métricas")
        
        # Aplica filtros
        df_filtrado = df[
            (df['Campaign type'].isin(tipo_campanha)) &
            (df['Campaign status'].isin(status_campanha))
        ]
        
        # Abas principais
        tab1, tab2, tab3 = st.tabs(["📋 Visão Geral", "📊 Análise por Métrica", "📝 Relatório Completo"])
        
        with tab1:
            st.subheader("Visão Geral das Campanhas")
            
            # Métricas rápidas
            col1, col2, col3 = st.columns(3)
            col1.metric("Total de Campanhas", len(df_filtrado))
            col2.metric("Campanhas Ativas", len(df_filtrado[df_filtrado['Campaign status'] == 'Active']))
            col3.metric("Campanhas Pausadas", len(df_filtrado[df_filtrado['Campaign status'] == 'Paused']))
            
            # Dados filtrados
            st.dataframe(df_filtrado, use_container_width=True)
        
        with tab2:
            st.subheader("Análise Detalhada por Métrica")
            
            # Seleciona métrica para análise
            metrica_selecionada = st.selectbox(
                "Selecione uma métrica para análise detalhada",
                options=colunas_numericas
            )
            
            if metrica_selecionada:
                # Estatísticas
                st.write(f"**Estatísticas para {metrica_selecionada}**")
                stats = metricas[metrica_selecionada]
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Média", f"{stats['média']:,.2f}")
                col2.metric("Mediana", f"{stats['mediana']:,.2f}")
                col3.metric("Mínimo", f"{stats['min']:,.2f}")
                col4.metric("Máximo", f"{stats['max']:,.2f}")
                
                # Boxplot
                if mostrar_boxplots:
                    st.subheader("Distribuição dos Valores")
                    criar_boxplot(df_filtrado, metrica_selecionada)
                
                # Top e Bottom performers
                st.subheader("Campanhas com Melhor Performance")
                top5 = df_filtrado.nlargest(5, metrica_selecionada)[['Campaign', metrica_selecionada]]
                st.dataframe(top5.style.format({metrica_selecionada: "{:,.2f}"}))
                
                st.subheader("Campanhas com Pior Performance")
                bottom5 = df_filtrado.nsmallest(5, metrica_selecionada)[['Campaign', metrica_selecionada]]
                st.dataframe(bottom5.style.format({metrica_selecionada: "{:,.2f}"}))
        
        with tab3:
            st.subheader("Relatório Completo de Performance")
            
            # Gera relatório
            relatorio = gerar_relatorio(df_filtrado, metricas, metricas_relatorio)
            
            # Mostra relatório
            st.markdown(relatorio)
            
            # Opção para download
            st.download_button(
                label="⬇️ Baixar Relatório",
                data=relatorio,
                file_name="relatorio_campanhas.md",
                mime="text/markdown"
            )

else:
    st.info("ℹ️ Por favor, carregue um arquivo CSV para começar a análise")
