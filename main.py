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

# Funções do aplicativo
def carregar_dados(arquivo):
    try:
        try:
            df = pd.read_csv(arquivo, skiprows=2)
        except UnicodeDecodeError:
            df = pd.read_csv(arquivo, skiprows=2, encoding='latin1')
            
        df = df.dropna(how='all')
        
        rename_dict = {
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
        }
        
        rename_dict = {k: v for k, v in rename_dict.items() if k in df.columns}
        df = df.rename(columns=rename_dict)
        
        for col in df.columns:
            if pd.api.types.is_object_dtype(df[col]):
                try:
                    df[col] = df[col].astype(str).str.replace(',', '.').str.replace('%', '').str.replace('R\$', '').str.replace(' ', '')
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except:
                    continue
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {str(e)}")
        return None

def calcular_metricas(df):
    metricas = {}
    if df.empty:
        return metricas
        
    colunas_numericas = df.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in colunas_numericas:
        try:
            metricas[col] = {
                'média': df[col].mean(),
                'mediana': df[col].median(),
                'desvio_padrao': df[col].std(),
                'min': df[col].min(),
                'max': df[col].max(),
                'q1': df[col].quantile(0.25),
                'q3': df[col].quantile(0.75)
            }
        except:
            continue
    
    return metricas

def criar_boxplot(df, coluna):
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
    try:
        plt.figure(figsize=(10, 6))
        
        valores = {
            'Mês Atual': dados_atual[metrica].mean(),
            'Mês Anterior': dados_anterior[metrica].mean()
        }
        
        try:
            variacao = ((valores['Mês Atual'] - valores['Mês Anterior']) / valores['Mês Anterior']) * 100
        except ZeroDivisionError:
            variacao = 0
        
        plt.bar(valores.keys(), valores.values(), color=['#4CAF50', '#2196F3'])
        
        for i, v in enumerate(valores.values()):
            plt.text(i, v, f"{v:,.2f}", ha='center', va='bottom')
        
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
    if not gemini_api_key:
        return "🔒 Relatório avançado desabilitado. Configure a API key do Gemini para ativar esta funcionalidade."
    
    try:
        dados_para_llm = ""
        dados_para_llm += "## Resumo Estatístico:\n"
        for col in colunas_selecionadas:
            if col in metricas:
                stats = metricas[col]
                dados_para_llm += f"- {col}: Média={stats['média']:.2f}, Mediana={stats['mediana']:.2f}, Min={stats['min']:.2f}, Max={stats['max']:.2f}\n"
        
        dados_para_llm += "\n## Melhores Campanhas:\n"
        for col in colunas_selecionadas[:3]:
            if col in df.columns and 'Campaign' in df.columns:
                top3 = df.nlargest(3, col)[['Campaign', col]]
                dados_para_llm += f"- {col}:\n"
                for _, row in top3.iterrows():
                    dados_para_llm += f"  - {row['Campaign']}: {row[col]:.2f}\n"
        
        model = GenerativeModel('gemini-1.5-flash')
        
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
        
        with st.spinner("🧠 Gerando relatório avançado com IA..."):
            response = model.generate_content(prompt)
            return response.text
        
    except Exception as e:
        return f"Erro ao gerar relatório: {str(e)}"

# Interface do usuário
if 'dados_atual' not in st.session_state:
    st.session_state.dados_atual = None
    st.session_state.dados_anterior = None

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

if st.session_state.dados_atual is not None:
    df = st.session_state.dados_atual
    metricas = calcular_metricas(df)
    colunas_numericas = [col for col in metricas.keys() if col in df.columns]
    
    with st.sidebar:
        st.header("🔧 Configurações de Análise")
        
        # Verificar se temos dados válidos
        if st.session_state.dados_atual is not None and not st.session_state.dados_atual.empty:
            df = st.session_state.dados_atual
            
            # Filtros
            st.subheader("Filtros")
            
            # Tipo de Campanha
            if 'Tipo_campanha' in df.columns:
                tipo_values = df['Tipo_campanha'].unique().tolist() if not df['Tipo_campanha'].empty else []
                tipo_campanha = st.multiselect(
                    "Tipo de Campanha",
                    options=tipo_values,
                    default=tipo_values
                )
            else:
                st.warning("Coluna 'Tipo de Campanha' não encontrada")
                tipo_campanha = []
            
            # Status da Campanha
            if 'Status' in df.columns:
                status_values = df['Status'].unique().tolist() if not df['Status'].empty else []
                status_campanha = st.multiselect(
                    "Status da Campanha",
                    options=status_values,
                    default=status_values
                )
            else:
                st.warning("Coluna 'Status' não encontrada")
                status_campanha = []
            
            mostrar_boxplots = st.checkbox("Mostrar boxplots das métricas")
        else:
            st.warning("Carregue os dados primeiro para configurar os filtros")
            tipo_campanha = []
            status_campanha = []
            mostrar_boxplots = False
    
    # Aplicar filtros apenas para colunas existentes
    df_filtrado = df.copy()
    if 'Tipo_campanha' in df.columns and tipo_campanha:
        df_filtrado = df_filtrado[df_filtrado['Tipo_campanha'].isin(tipo_campanha)]
    if 'Status' in df.columns and status_campanha:
        df_filtrado = df_filtrado[df_filtrado['Status'].isin(status_campanha)]

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Visão Geral", "📊 Análise por Métrica", "🔄 Comparativo Mensal", "🧠 Relatório Avançado"])
    
    with tab1:
        st.subheader("Visão Geral das Campanhas - Mês Atual")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Campanhas", len(df_filtrado))
        
        if 'Status' in df_filtrado.columns:
            status_values = df_filtrado['Status'].unique()
            if 'Ativo' in status_values:
                col2.metric("Campanhas Ativas", len(df_filtrado[df_filtrado['Status'] == 'Ativo']))
            if 'Pausado' in status_values:
                col3.metric("Campanhas Pausadas", len(df_filtrado[df_filtrado['Status'] == 'Pausado']))
        
        st.dataframe(df_filtrado, use_container_width=True)
    
    with tab2:
        st.subheader("Análise Detalhada por Métrica - Mês Atual")
        
        if colunas_numericas:
            metrica_selecionada = st.selectbox(
                "Selecione uma métrica para análise detalhada",
                options=colunas_numericas
            )
            
            if metrica_selecionada in metricas:
                stats = metricas[metrica_selecionada]
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Média", f"{stats['média']:,.2f}")
                col2.metric("Mediana", f"{stats['mediana']:,.2f}")
                col3.metric("Mínimo", f"{stats['min']:,.2f}")
                col4.metric("Máximo", f"{stats['max']:,.2f}")
                
                if mostrar_boxplots:
                    st.subheader("Distribuição dos Valores")
                    criar_boxplot(df_filtrado, metrica_selecionada)
                
                if 'Campaign' in df_filtrado.columns:
                    st.subheader("Campanhas acima da média")
                    top5 = df_filtrado.nlargest(5, metrica_selecionada)[['Campaign', metrica_selecionada]]
                    st.dataframe(top5.style.format({metrica_selecionada: "{:,.2f}"}))
                    
                    st.subheader("Campanhas abaixo da média")
                    bottom5 = df_filtrado.nsmallest(5, metrica_selecionada)[['Campaign', metrica_selecionada]]
                    st.dataframe(bottom5.style.format({metrica_selecionada: "{:,.2f}"}))
        else:
            st.warning("Nenhuma métrica numérica disponível para análise")
    
    with tab3:
        st.subheader("Comparativo Mensal")
        
        if st.session_state.dados_anterior is not None:
            df_anterior_filtrado = st.session_state.dados_anterior.copy()
            
            # Aplicar mesmos filtros ao mês anterior
            if 'Tipo_campanha' in df_anterior_filtrado.columns and tipo_campanha:
                df_anterior_filtrado = df_anterior_filtrado[df_anterior_filtrado['Tipo_campanha'].isin(tipo_campanha)]
            if 'Status' in df_anterior_filtrado.columns and status_campanha:
                df_anterior_filtrado = df_anterior_filtrado[df_anterior_filtrado['Status'].isin(status_campanha)]

            if colunas_numericas:
                metrica_comparacao = st.selectbox(
                    "Selecione uma métrica para comparação",
                    options=colunas_numericas,
                    key="comparacao_metrica"
                )
                
                if metrica_comparacao in df_filtrado.columns and metrica_comparacao in df_anterior_filtrado.columns:
                    variacao = criar_grafico_comparativo(df_filtrado, df_anterior_filtrado, metrica_comparacao)
                    
                    st.subheader("Análise Detalhada da Comparação")
                    
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
                    
                    df_comparativo = pd.DataFrame({
                        'Mês Atual': stats_atual,
                        'Mês Anterior': stats_anterior
                    }).T
                    
                    try:
                        df_comparativo['Variação (%)'] = ((df_comparativo.loc['Mês Atual'] - df_comparativo.loc['Mês Anterior']) / 
                                                        df_comparativo.loc['Mês Anterior']) * 100
                    except:
                        df_comparativo['Variação (%)'] = 0
                    
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
            if metricas_relatorio:
                relatorio = gerar_relatorio_llm(df_filtrado, metricas, metricas_relatorio, tipo_relatorio)
                st.markdown(relatorio)
                
                st.download_button(
                    label="⬇️ Baixar Relatório Completo",
                    data=relatorio,
                    file_name=f"relatorio_{tipo_relatorio}_campanhas.md",
                    mime="text/markdown"
                )
            else:
                st.warning("Selecione pelo menos uma métrica para gerar o relatório")
        else:
            st.info("Clique no botão acima para gerar um relatório avançado com análise de IA")

else:
    st.info("ℹ️ Por favor, carregue pelo menos o relatório do mês atual para começar a análise")

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
