import streamlit as st
import pandas as pd
import numpy as np
import os
from google.generativeai import GenerativeModel
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Configuração da página
st.set_page_config(
    layout="wide",
    page_title="Analytics de Campanhas",
    page_icon="📊"
)

# Título principal
st.title("📊 Analytics Avançado de Campanhas Digitais")

# Verifica se a API key do Gemini está configurada
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    st.warning("⚠️ Chave da API Gemini não encontrada. O relatório avançado será limitado.")

# Funções do aplicativo ==============================================

def carregar_dados(arquivo):
    """Carrega e prepara o arquivo CSV"""
    try:
        df = pd.read_csv(arquivo, skiprows=2)
        df = df.dropna(how='all')
        
        for col in df.columns:
            if df[col].dtype == 'object':
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
        if col in ['Campaign ID']:
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
    try:
        plt.figure(figsize=(8, 4))
        sns.boxplot(x=df[coluna])
        plt.title(f'Distribuição de {coluna}')
        plt.xlabel('Valor')
        st.pyplot(plt)
        plt.close()
    except Exception as e:
        st.error(f"Erro ao criar gráfico: {str(e)}")

def criar_grafico_evolucao(dados_comparativos, metrica):
    """Cria um gráfico de evolução da métrica selecionada"""
    try:
        plt.figure(figsize=(10, 6))
        
        # Prepara os dados para o gráfico
        datas = []
        valores = []
        
        for data, df in dados_comparativos.items():
            if metrica in df.columns:
                datas.append(data)
                valores.append(df[metrica].mean())
        
        if len(datas) > 1:
            plt.plot(datas, valores, marker='o', linestyle='-')
            plt.title(f'Evolução da métrica: {metrica}')
            plt.xlabel('Data do Relatório')
            plt.ylabel('Valor Médio')
            plt.xticks(rotation=45)
            plt.grid(True)
            st.pyplot(plt)
            plt.close()
        else:
            st.warning("São necessários pelo menos 2 conjuntos de dados para mostrar a evolução")
    except Exception as e:
        st.error(f"Erro ao criar gráfico de evolução: {str(e)}")

def gerar_relatorio_llm(df, metricas, colunas_selecionadas, tipo_relatorio):
    """Gera um relatório analítico usando LLM"""
    if not gemini_api_key:
        return "🔒 Relatório avançado desabilitado. Configure a API key do Gemini para ativar esta funcionalidade."
    
    try:
        # Prepara os dados para o LLM
        dados_para_llm = ""
        
        # Resumo estatístico
        dados_para_llm += "## Resumo Estatístico:\n"
        for col in colunas_selecionadas:
            if col in metricas:
                stats = metricas[col]
                dados_para_llm += f"- {col}: Média={stats['média']:.2f}, Mediana={stats['mediana']:.2f}, Min={stats['min']:.2f}, Max={stats['max']:.2f}\n"
        
        # Top e bottom performers
        dados_para_llm += "\n## Melhores Campanhas:\n"
        for col in colunas_selecionadas[:3]:  # Limita a 3 métricas para não ficar muito longo
            if col in df.columns:
                top3 = df.nlargest(3, col)[['Campaign', col]]
                dados_para_llm += f"- {col}:\n"
                for _, row in top3.iterrows():
                    dados_para_llm += f"  - {row['Campaign']}: {row[col]:.2f}\n"
        
        # Inicializa o modelo Gemini
        model = GenerativeModel('gemini-1.5-flash')
        
        # Prompt específico baseado no tipo de relatório selecionado
        if tipo_relatorio == "técnico":
            prompt = f"""
            Você é um analista de marketing digital senior. Analise os dados de campanhas e gere um relatório TÉCNICO detalhado em português com:
            
            1. Introdução com visão geral
            2. Análise de cada métrica selecionada
            3. Insights sobre desempenho
            4. Recomendações técnicas específicas
            5. Conclusão com resumo executivo
            
            Dados:
            {dados_para_llm}
            
            Formate o relatório em markdown com títulos e subtítulos. Seja detalhado e técnico.
            """
        else:
            prompt = f"""
            Você é um estrategista de marketing. Crie um relatório GERENCIAL em português com:
            
            1. Visão geral simplificada
            2. Principais destaques e preocupações
            3. Análise estratégica do desempenho
            4. Recomendações de alto nível
            5. Próximos passos sugeridos
            
            Dados:
            {dados_para_llm}
            
            Formate o relatório em markdown. Use linguagem acessível para não-especialistas.
            """
        
        # Gera o conteúdo com o Gemini
        with st.spinner("🧠 Gerando relatório avançado com IA..."):
            response = model.generate_content(prompt)
            return response.text
        
    except Exception as e:
        return f"Erro ao gerar relatório: {str(e)}"

# Interface do usuário ===============================================

# Sessão para armazenar os dados carregados
if 'dados_comparativos' not in st.session_state:
    st.session_state.dados_comparativos = {}
    st.session_state.ultimo_arquivo = None

# Upload de múltiplos arquivos
arquivos = st.file_uploader(
    "📤 Carregue seus relatórios de campanhas (formato CSV)",
    type=["csv"],
    help="O arquivo deve seguir o formato padrão dos relatórios do Google Ads",
    accept_multiple_files=True
)

if arquivos:
    for arquivo in arquivos:
        # Usa a data de upload como identificador se não houver data no arquivo
        data_arquivo = datetime.now().strftime("%Y-%m-%d %H:%M")
        df = carregar_dados(arquivo)
        
        if df is not None:
            st.session_state.dados_comparativos[data_arquivo] = df
            st.session_state.ultimo_arquivo = data_arquivo
            st.success(f"✅ Dados de {data_arquivo} carregados com sucesso!")

if st.session_state.dados_comparativos:
    # Mostra qual é o arquivo mais recente
    if st.session_state.ultimo_arquivo:
        st.sidebar.markdown(f"**Último arquivo carregado:** {st.session_state.ultimo_arquivo}")
    
    # Obtém o último DataFrame carregado para análise principal
    df = st.session_state.dados_comparativos[st.session_state.ultimo_arquivo]
    metricas = calcular_metricas(df)
    colunas_numericas = [col for col in metricas.keys() if col != 'Campaign ID']
    
    with st.sidebar:
        st.header("🔧 Configurações de Análise")
        
        # Seleção de métricas
        metricas_relatorio = st.multiselect(
            "Selecione as métricas para análise",
            options=colunas_numericas,
            default=colunas_numericas[:5]
        )
        
        # Tipo de relatório
        tipo_relatorio = st.radio(
            "Tipo de relatório",
            options=["técnico", "gerencial"],
            index=0
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
        
        mostrar_boxplots = st.checkbox("Mostrar boxplots das métricas")
    
    # Aplica filtros
    df_filtrado = df[
        (df['Campaign type'].isin(tipo_campanha)) &
        (df['Campaign status'].isin(status_campanha))
    ]
    
    # Abas principais
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Visão Geral", "📊 Análise por Métrica", "📈 Evolução Mensal", "🧠 Relatório Avançado"])
    
    with tab1:
        st.subheader("Visão Geral das Campanhas")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Campanhas", len(df_filtrado))
        col2.metric("Campanhas Ativas", len(df_filtrado[df_filtrado['Campaign status'] == 'Active']))
        col3.metric("Campanhas Pausadas", len(df_filtrado[df_filtrado['Campaign status'] == 'Paused']))
        
        st.dataframe(df_filtrado, use_container_width=True)
    
    with tab2:
        st.subheader("Análise Detalhada por Métrica")
        
        metrica_selecionada = st.selectbox(
            "Selecione uma métrica para análise detalhada",
            options=colunas_numericas
        )
        
        if metrica_selecionada:
            stats = metricas[metrica_selecionada]
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Média", f"{stats['média']:,.2f}")
            col2.metric("Mediana", f"{stats['mediana']:,.2f}")
            col3.metric("Mínimo", f"{stats['min']:,.2f}")
            col4.metric("Máximo", f"{stats['max']:,.2f}")
            
            if mostrar_boxplots:
                st.subheader("Distribuição dos Valores")
                criar_boxplot(df_filtrado, metrica_selecionada)
            
            st.subheader("Campanhas acima da média")
            top5 = df_filtrado.nlargest(5, metrica_selecionada)[['Campaign', metrica_selecionada]]
            st.dataframe(top5.style.format({metrica_selecionada: "{:,.2f}"}))
            
            st.subheader("Campanhas abaixo da média")
            bottom5 = df_filtrado.nsmallest(5, metrica_selecionada)[['Campaign', metrica_selecionada]]
            st.dataframe(bottom5.style.format({metrica_selecionada: "{:,.2f}"}))
    
    with tab3:
        st.subheader("Evolução Mensal das Métricas")
        
        if len(st.session_state.dados_comparativos) > 1:
            metrica_evolucao = st.selectbox(
                "Selecione uma métrica para análise de evolução",
                options=colunas_numericas,
                key="evolucao_metrica"
            )
            
            if metrica_evolucao:
                criar_grafico_evolucao(st.session_state.dados_comparativos, metrica_evolucao)
                
                # Tabela comparativa
                st.subheader("Comparativo Mensal")
                comparativo_data = []
                
                for data, df in st.session_state.dados_comparativos.items():
                    if metrica_evolucao in df.columns:
                        comparativo_data.append({
                            'Data': data,
                            'Média': df[metrica_evolucao].mean(),
                            'Mediana': df[metrica_evolucao].median(),
                            'Mínimo': df[metrica_evolucao].min(),
                            'Máximo': df[metrica_evolucao].max()
                        })
                
                df_comparativo = pd.DataFrame(comparativo_data)
                st.dataframe(df_comparativo.style.format({
                    'Média': '{:,.2f}',
                    'Mediana': '{:,.2f}',
                    'Mínimo': '{:,.2f}',
                    'Máximo': '{:,.2f}'
                }))
        else:
            st.info("Carregue pelo menos dois conjuntos de dados para comparar a evolução mensal")
    
    with tab4:
        st.subheader("Relatório Avançado com IA")
        
        if st.button("Gerar Relatório com Análise Avançada"):
            relatorio = gerar_relatorio_llm(df_filtrado, metricas, metricas_relatorio, tipo_relatorio)
            
            st.markdown(relatorio)
            
            st.download_button(
                label="⬇️ Baixar Relatório Completo",
                data=relatorio,
                file_name=f"relatorio_{tipo_relatorio}_campanhas.md",
                mime="text/markdown"
            )
        else:
            st.info("Clique no botão acima para gerar um relatório avançado com análise de IA")

else:
    st.info("ℹ️ Por favor, carregue um arquivo CSV para começar a análise")

# Instruções para configurar a API
if not gemini_api_key:
    st.markdown("""
    ## 🔑 Configuração da API Gemini
    Para habilitar o relatório avançado com IA:
    1. Obtenha uma API key do Google Gemini
    2. Configure como variável de ambiente:
       ```bash
       export GEMINI_API_KEY='sua_chave_aqui'
       ```
    3. Reinicie o aplicativo
    """)
