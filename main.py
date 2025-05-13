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
        
        # Renomear colunas para nomes mais simples
        df = df.rename(columns={
            'Status da campanha': 'Status',
            'Campanha': 'Campaign',
            'Nome do orçamento': 'Nome_orcamento',
            'Código da moeda': 'Moeda',
            'Orçamento': 'Orcamento',
            'Tipo de orçamento': 'Tipo_orcamento',
            'Motivos do status': 'Motivos_status',
            'Pontuação de otimização': 'Pontuacao_otimizacao',
            'Tipo de campanha': 'Tipo_campanha',
            'CPV médio': 'CPV_medio',
            'Interações': 'Interacoes',
            'Taxa de interação': 'Taxa_interacao',
            'Custo': 'Custo',
            'Impr.': 'Impressoes',
            'Cliques': 'Cliques',
            'Conversões': 'Conversoes',
            'CTR': 'CTR',
            'CPM médio': 'CPM_medio',
            'CPC méd.': 'CPC_medio',
            'Custo / conv.': 'Custo_por_conversao',
            'Custo médio': 'Custo_medio',
            'Engajamentos': 'Engajamentos',
            'IS parte sup. pesq.': 'IS_parte_superior',
            'IS 1ª posição pesq.': 'IS_primeira_posicao',
            'Visualizações': 'Visualizacoes',
            'Tipo de estratégia de lances': 'Estrategia_lances',
            'Taxa de conv.': 'Taxa_conversao'
        })
        
        # Converter colunas numéricas
        for col in df.columns:
            # Verifica se a coluna é do tipo objeto (string)
            if pd.api.types.is_object_dtype(df[col]):
                try:
                    # Remove caracteres especiais e converte para numérico
                    df[col] = df[col].astype(str).str.replace(',', '.').str.replace('%', '').str.replace(' ', '')
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

def criar_grafico_comparativo(dados_atual, dados_anterior, metrica):
    """Cria um gráfico comparativo entre os dois períodos"""
    try:
        plt.figure(figsize=(10, 6))
        
        # Valores para comparação
        valores = {
            'Mês Atual': dados_atual[metrica].mean(),
            'Mês Anterior': dados_anterior[metrica].mean()
        }
        
        # Cálculo da variação percentual
        variacao = ((valores['Mês Atual'] - valores['Mês Anterior']) / valores['Mês Anterior']) * 100
        
        # Gráfico de barras
        plt.bar(valores.keys(), valores.values(), color=['#4CAF50', '#2196F3'])
        
        # Adiciona rótulos com os valores
        for i, v in enumerate(valores.values()):
            plt.text(i, v, f"{v:,.2f}", ha='center', va='bottom')
        
        # Configurações do gráfico
        plt.title(f"Comparação: {metrica}\nVariação: {variacao:.1f}%")
        plt.ylabel('Valor Médio')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        st.pyplot(plt)
        plt.close()
        
        return variacao
    except Exception as e:
        st.error(f"Erro ao criar gráfico comparativo: {str(e)}")
        return 0

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
if 'dados_atual' not in st.session_state:
    st.session_state.dados_atual = None
    st.session_state.dados_anterior = None

# Seção de upload de arquivos
col1, col2 = st.columns(2)

with col1:
    st.subheader("📅 Mês Atual (Mais Recente)")
    arquivo_atual = st.file_uploader(
        "Carregue o relatório do mês atual",
        type=["csv"],
        key="uploader_atual"
    )
    if arquivo_atual:
        df_atual = carregar_dados(arquivo_atual)
        if df_atual is not None:
            st.session_state.dados_atual = df_atual
            st.success("✅ Dados do mês atual carregados com sucesso!")

with col2:
    st.subheader("🗓️ Mês Anterior")
    arquivo_anterior = st.file_uploader(
        "Carregue o relatório do mês anterior",
        type=["csv"],
        key="uploader_anterior"
    )
    if arquivo_anterior:
        df_anterior = carregar_dados(arquivo_anterior)
        if df_anterior is not None:
            st.session_state.dados_anterior = df_anterior
            st.success("✅ Dados do mês anterior carregados com sucesso!")

# Verifica se temos dados para análise
if st.session_state.dados_atual is not None:
    df = st.session_state.dados_atual
    metricas = calcular_metricas(df)
    
    # Na parte onde definimos as colunas numéricas (substitua a linha original)
    colunas_numericas = [col for col in df.select_dtypes(include=[np.number]).columns.tolist() if col in df.columns]
    
    # E na seção do multiselect, modifique para:
    with st.sidebar:
        st.header("🔧 Configurações de Análise")
        
        # Verifica se existem colunas numéricas disponíveis
        metricas_disponiveis = colunas_numericas if len(colunas_numericas) > 0 else []
        
        # Seleção de métricas com verificação de valores padrão
        default_metrics = ['Custo', 'Cliques', 'Impressoes', 'CTR', 'Conversoes']
        metricas_padrao = [m for m in default_metrics if m in metricas_disponiveis]
        
        metricas_relatorio = st.multiselect(
            "Selecione as métricas para análise",
            options=metricas_disponiveis,
            default=metricas_padrao[:5] if len(metricas_padrao) > 0 else None
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
            options=df['Tipo_campanha'].unique(),
            default=df['Tipo_campanha'].unique()
        )
        
        status_campanha = st.multiselect(
            "Status da Campanha",
            options=df['Status'].unique(),
            default=df['Status'].unique()
        )
        
        mostrar_boxplots = st.checkbox("Mostrar boxplots das métricas")
    
    # Aplica filtros
    df_filtrado = df[
        (df['Tipo_campanha'].isin(tipo_campanha)) &
        (df['Status'].isin(status_campanha))
    ]
    
    # Abas principais
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Visão Geral", "📊 Análise por Métrica", "🔄 Comparativo Mensal", "🧠 Relatório Avançado"])
    
    with tab1:
        st.subheader("Visão Geral das Campanhas - Mês Atual")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Campanhas", len(df_filtrado))
        col2.metric("Campanhas Ativas", len(df_filtrado[df_filtrado['Status'] == 'Ativo']))
        col3.metric("Campanhas Pausadas", len(df_filtrado[df_filtrado['Status'] == 'Pausado']))
        
        st.dataframe(df_filtrado, use_container_width=True)
    
    with tab2:
        st.subheader("Análise Detalhada por Métrica - Mês Atual")
        
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
        st.subheader("Comparativo Mensal")
        
        if st.session_state.dados_anterior is not None:
            # Aplica os mesmos filtros ao mês anterior
            df_anterior_filtrado = st.session_state.dados_anterior[
                (st.session_state.dados_anterior['Tipo_campanha'].isin(tipo_campanha)) &
                (st.session_state.dados_anterior['Status'].isin(status_campanha))
            ]
            
            metrica_comparacao = st.selectbox(
                "Selecione uma métrica para comparação",
                options=colunas_numericas,
                key="comparacao_metrica"
            )
            
            if metrica_comparacao:
                variacao = criar_grafico_comparativo(df_filtrado, df_anterior_filtrado, metrica_comparacao)
                
                # Tabela comparativa detalhada
                st.subheader("Análise Detalhada da Comparação")
                
                # Calcula estatísticas para ambos os períodos
                stats_atual = {
                    'Média': df_filtrado[metrica_comparacao].mean(),
                    'Mediana': df_filtrado[metrica_comparacao].median(),
                    'Mínimo': df_filtrado[metrica_comparacao].min(),
                    'Máximo': df_filtrado[metrica_comparacao].max(),
                    'Desvio Padrão': df_filtrado[metrica_comparacao].std()
                }
                
                stats_anterior = {
                    'Média': df_anterior_filtrado[metrica_comparacao].mean(),
                    'Mediana': df_anterior_filtrado[metrica_comparacao].median(),
                    'Mínimo': df_anterior_filtrado[metrica_comparacao].min(),
                    'Máximo': df_anterior_filtrado[metrica_comparacao].max(),
                    'Desvio Padrão': df_anterior_filtrado[metrica_comparacao].std()
                }
                
                # Cria DataFrame comparativo
                df_comparativo = pd.DataFrame({
                    'Mês Atual': stats_atual,
                    'Mês Anterior': stats_anterior
                }).T
                
                # Calcula variações
                df_comparativo['Variação (%)'] = ((df_comparativo.loc['Mês Atual'] - df_comparativo.loc['Mês Anterior']) / 
                                                df_comparativo.loc['Mês Anterior']) * 100
                
                # Formatação condicional para a variação
                def color_variation(val):
                    color = 'red' if val < 0 else 'green' if val > 0 else 'gray'
                    return f'color: {color}'
                
                st.dataframe(
                    df_comparativo.style.format({
                        'Média': '{:,.2f}',
                        'Mediana': '{:,.2f}',
                        'Mínimo': '{:,.2f}',
                        'Máximo': '{:,.2f}',
                        'Desvio Padrão': '{:,.2f}',
                        'Variação (%)': '{:,.1f}%'
                    }).applymap(color_variation, subset=['Variação (%)'])
                )
        else:
            st.info("ℹ️ Carregue os dados do mês anterior para habilitar a comparação mensal")
    
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
    st.info("ℹ️ Por favor, carregue pelo menos o relatório do mês atual para começar a análise")

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
