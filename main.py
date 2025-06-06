import streamlit as st
import pandas as pd
import numpy as np
import os
from google.generativeai import GenerativeModel
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId

# Configuração da página
st.set_page_config(
    layout="wide",
    page_title="Analytics de Campanhas",
    page_icon="📊"
)

rel_metrica = '''
###BEGIN RELACAO METRICA VS TIPO DE CAMPANHA###
            📌 Search (Pesquisa)
            CTR (Taxa de Cliques) - Principal indicador de relevância do anúncio
            
            Conversões - Objetivo final das campanhas de busca
            
            CPC médio (Custo por Clique) - Custo da aquisição de tráfego
            
            Custo por conversão - Eficiência no ROI
            
            IS parte superior pesquisa (Impression Share) - Visibilidade nos melhores posicionamentos
            
            Taxa de conversão - Eficácia da landing page
            
            🎯 Performance Max (Pmax)
            Conversões - Métrica principal deste tipo de campanha
            
            Custo por conversão - Eficiência de custo
            
            CTR - Engajamento com os anúncios
            
            Impressões - Alcance da campanha
            
            Taxa de conversão - Eficácia do funnel
            
            📢 Display
            Impressões - Alcance da campanha
            
            CPM médio (Custo por Mil Impressões) - Custo da exposição
            
            CTR - Engajamento com os banners
            
            Conversões (se for o objetivo)
            
            Visualizações (para creatives interativos)
            
            📹 Video
            Visualizações (Views) - Pessoas que assistiram o vídeo
            
            CPV médio (Custo por Visualização) - Custo da atenção
            
            Engajamentos - Interações com o vídeo
            
            Taxa de interação - % de quem interagiu
            
            Conversões (se for campanha de conversão)
            
            🔍 Discovery
            CTR - Relevância dos anúncios
            
            Conversões - Resultados concretos
            
            CPC médio - Custo da descoberta
            
            Impressões - Alcance orgânico+paid
            
            Taxa de conversão - Eficácia pós-clique
            
            🏷️ Alcance (Reach)
            Impressões - Quantas vezes foi exibido
            
            CPM médio - Custo do alcance
            
            Frequência (calculada: Impressões/Únicos) - Número médio de visualizações por usuário
            
            Engajamentos - Interações com o conteúdo
            
            📊 Métricas Universais Importantes
            (Relevantes para todos os tipos)
            
            Custo - Investimento total
            
            Orçamento vs Custo - Comparação planejado vs realizado
            
            Pontuação de otimização - Saúde geral da campanha
            
            Status da campanha - Campanhas ativas/pausadas
            
            📉 Métricas de Qualidade
            IS parte superior pesquisa (para Search) - Posicionamento premium
            
            IS 1ª posição pesquisa (para Search) - Liderança nos resultados
            
            Taxa de interação (para Video/Display) - Engajamento qualificado
            ###END RELACAO METRICA VS CAMPANHA###
'''

# Título principal
st.title("📊 Analytics Avançado de Campanhas Digitais")

# Conexão com MongoDB
client = MongoClient("mongodb+srv://gustavoromao3345:RqWFPNOJQfInAW1N@cluster0.5iilj.mongodb.net/auto_doc?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE&tlsAllowInvalidCertificates=true")
db = client['arquivos_planejamento']
collection = db['auto_doc']
banco = client["arquivos_planejamento"]
db_clientes = banco["clientes"]  # info clientes

# Verifica se a API key do Gemini está configurada
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    st.warning("⚠️ Chave da API Gemini não encontrada. O relatório avançado será limitado.")

# Funções do aplicativo ==============================================

# No início do código, adicione uma função para detectar o tipo de campanha pelo nome
def detectar_tipo_campanha(nome_campanha):
    nome = nome_campanha.lower()
    if 'search' in nome:
        return 'Search'
    elif 'alcance' in nome or 'reach' in nome:
        return 'Alcance'
    elif 'conversao' in nome or 'conversão' in nome or 'conversion' in nome:
        return 'Conversão'
    elif 'display' in nome:
        return 'Display'
    elif 'video' in nome or 'vídeo' in nome:
        return 'Video'
    elif 'discovery' in nome:
        return 'Discovery'
    elif 'pmax' in nome or 'performance max' in nome:
        return 'Performance Max'
    else:
        return 'Outros'



def carregar_dados(arquivo):
    """Carrega e prepara o arquivo CSV"""
    try:
        df = pd.read_csv(arquivo, skiprows=2)
        df = df.dropna(how='all')
        
        # Renomear colunas para nomes consistentes
        df.columns = [
            'Status da campanha', 'Campanha', 'Nome do orçamento', 'Código da moeda', 
            'Orçamento', 'Tipo de orçamento', 'Status', 'Motivos do status', 
            'Pontuação de otimização', 'Tipo de campanha', 'CPV médio', 'Interações', 
            'Taxa de interação', 'Custo', 'Impressões', 'Cliques', 'Conversões', 
            'CTR', 'CPM médio', 'CPC médio', 'Custo por conversão', 'Custo médio', 
            'Engajamentos', 'IS parte superior pesquisa', 'IS 1ª posição pesquisa', 
            'Visualizações', 'Tipo de estratégia de lances', 'Taxa de conversão'
        ]
        
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

def salvar_relatorio_mongodb(relatorio_data):
    """Salva o relatório no MongoDB"""
    try:
        result = collection.insert_one(relatorio_data)
        return str(result.inserted_id)
    except Exception as e:
        st.error(f"Erro ao salvar no MongoDB: {str(e)}")
        return None

def gerar_relatorio_llm(df, metricas, colunas_selecionadas, tipo_relatorio, cliente_info=None, df_anterior=None):
    """Gera um relatório analítico usando LLM e salva no MongoDB"""
    if not gemini_api_key:
        return "🔒 Relatório avançado desabilitado. Configure a API key do Gemini para ativar esta funcionalidade."
    
    try:
        # Prepara os dados para o LLM
        dados_para_llm = ""
        
        # Resumo estatístico do período atual
        dados_para_llm += "## Resumo Estatístico - Mês Atual:\n"
        for col in colunas_selecionadas:
            if col in metricas:
                stats = metricas[col]
                dados_para_llm += f"- {col}: Média={stats['média']:.2f}, Mediana={stats['mediana']:.2f}, Min={stats['min']:.2f}, Max={stats['max']:.2f}\n"
        
        # Se tivermos dados do mês anterior, adicionamos análise comparativa
        if df_anterior is not None:
            metricas_anterior = calcular_metricas(df_anterior)
            dados_para_llm += "\n## Análise Comparativa Mensal:\n"
            
            # Calcula variações para cada métrica
            for col in colunas_selecionadas:
                if col in metricas and col in metricas_anterior:
                    media_atual = metricas[col]['média']
                    media_anterior = metricas_anterior[col]['média']
                    variacao = ((media_atual - media_anterior) / media_anterior) * 100 if media_anterior != 0 else 0
                    
                    dados_para_llm += (f"- {col}: {media_atual:.2f} (Mês Atual) vs {media_anterior:.2f} (Mês Anterior) → "
                                      f"{'↑' if variacao > 0 else '↓'} {abs(variacao):.1f}%\n")
        
        # Top e bottom performers
        dados_para_llm += "\n## Melhores Campanhas - Mês Atual:\n"
        for col in colunas_selecionadas[:3]:  # Limita a 3 métricas para não ficar muito longo
            if col in df.columns:
                top3 = df.nlargest(3, col)[['Campanha', col]]
                dados_para_llm += f"- {col}:\n"
                for _, row in top3.iterrows():
                    dados_para_llm += f"  - {row['Campanha']}: {row[col]:.2f}\n"
        
        # Análise de correlação entre métricas (quando temos ambos períodos)
        if df_anterior is not None:
            dados_para_llm += "\n## Insights de Correlação:\n"
            dados_para_llm += "- Comparação automática entre variações de métricas:\n"
            
            # Calcula variações percentuais para todas as métricas
            variacoes = {}
            for col in colunas_selecionadas:
                if col in metricas and col in metricas_anterior:
                    media_atual = metricas[col]['média']
                    media_anterior = metricas_anterior[col]['média']
                    variacoes[col] = ((media_atual - media_anterior) / media_anterior) * 100 if media_anterior != 0 else 0
            
            # Adiciona exemplos de insights combinados
            dados_para_llm += "  - Exemplo de análise combinada que será gerada pelo LLM:\n"
            dados_para_llm += "    * Se CTR aumentou mas Conversões caíram, pode indicar tráfego menos qualificado\n"
            dados_para_llm += "    * Se Custo por Conversão caiu e Conversões aumentaram, indica eficiência melhorada\n"
            dados_para_llm += "    * Se Impressões caíram mas Engajamentos aumentaram, pode indicar público mais segmentado\n"
        
        # Inicializa o modelo Gemini
        model = GenerativeModel('gemini-2.0-flash')
        
        # Gera o conteúdo com o Gemini
        with st.spinner("🧠 Gerando relatório avançado com IA..."):
            # Dicionário para armazenar todas as partes do relatório
            relatorio_completo = {
                "partes": [],
                "texto_completo": ""
            }
            
            # Gera cada parte do relatório
            prompts = []
            if tipo_relatorio == "técnico":
                prompts = [
                    ("1. Introdução com visão geral", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    
                    Você é um analista de marketing digital senior. Gere a introdução de um relatório TÉCNICO detalhado em português com:
                    - Visão geral do desempenho das campanhas
                    - Contexto sobre os dados analisados
                    - Destaque inicial dos pontos mais relevantes
                    
                    Dados: {dados_para_llm}
                    
                    """),
                    ("2. Análise de cada métrica selecionada", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    Faça uma análise técnica detalhada de cada métrica selecionada, incluindo:
                    - Significado de cada métrica
                    - Performance em relação aos benchmarks do setor
                    - Relação com o tipo de campanha
                    
                    Dados: {dados_para_llm}
 
                    """),
                    ("3. Comparativo mensal detalhado", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    Analise comparativamente os dados com o mês anterior (quando disponível):
                    - Variações percentuais significativas
                    - Tendências identificadas
                    - Possíveis causas para as variações
                    
                    Dados: {dados_para_llm}

                    """),
                    ("4. Insights sobre correlações", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    Identifique correlações importantes entre as métricas:
                    - Relações causa-efeito
                    - Padrões de desempenho
                    - Anomalias e outliers
                    
                    Dados: {dados_para_llm}
        
                    """),
                    ("5. Recomendações técnicas", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    Gere recomendações técnicas específicas baseadas na análise:
                    - Ajustes em campanhas
                    - Otimizações sugeridas
                    - Alertas sobre problemas identificados
                    
                    Dados: {dados_para_llm}
 
                    """),
                    ("6. Conclusão com resumo executivo", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    Conclua com um resumo executivo técnico:
                    - Principais achados
                    - Recomendações prioritárias
                    - Próximos passos sugeridos
                    
                    Dados: {dados_para_llm}

                    """)
                ]
            else:
                prompts = [
                    ("1. Visão geral simplificada", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    Você é um estrategista de marketing. Gere uma visão geral simplificada em português com:
                    - Principais resultados
                    - Destaques e preocupações
                    - Contexto estratégico
                    
                    Dados: {dados_para_llm}
        
                    """),
                    ("2. Principais destaques e preocupações", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    Destaque os pontos mais relevantes e preocupações:
                    - Comparações mensais
                    - Variações significativas
                    - Impacto estratégico dado o tipo de campanha
                    - Alinhamento com objetivos dado o tipo de campanha
                    
                    Dados: {dados_para_llm}

                    """),
                    ("3. Análise estratégica do desempenho", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    Analise o desempenho com foco em tendências:
                    - Padrões de longo prazo
                    - Eficácia estratégica
                    - Alinhamento com objetivos dado o tipo de campanha
                    
                    Dados: {dados_para_llm}

                    """),
                    ("4. Relações entre métricas", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    Explique como as métricas se relacionam e impactam os resultados:
                    - Conexões importantes
                    - Trade-offs identificados
                    - Sinergias encontradas
                    
                    Dados: {dados_para_llm}

                    """),
                    ("5. Recomendações de alto nível", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    Gere recomendações estratégicas:
                    - Direcionamentos gerais
                    - Priorizações sugeridas
                    - Ajustes recomendados
                    
                    Dados: {dados_para_llm}

                    """),
                    ("6. Próximos passos sugeridos", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    Defina os próximos passos estratégicos:
                    - Ações imediatas
                    - Monitoramentos necessários
                    - Planejamento futuro
                    
                    Dados: {dados_para_llm}

                    """)
                ]
            
            # Gera cada parte do relatório
            for titulo, prompt in prompts:
                with st.spinner(f"Gerando {titulo.lower()}..."):
                    response = model.generate_content(prompt)
                    parte_relatorio = {
                        "titulo": titulo,
                        "conteudo": response.text
                    }
                    relatorio_completo["partes"].append(parte_relatorio)
                    relatorio_completo["texto_completo"] += f"\n\n## {titulo}\n\n{response.text}"
            
            # Prepara os dados para salvar no MongoDB
            relatorio_data = {
                "tipo": tipo_relatorio,
                "partes": relatorio_completo["partes"],
                "texto_completo": relatorio_completo["texto_completo"],
                "metricas_analisadas": colunas_selecionadas,
                "data_geracao": datetime.now(),
                "cliente": cliente_info if cliente_info else "Não especificado",
                "status": "ativo",
                "comparativo_mensal": df_anterior is not None
            }
            
            # Salva no MongoDB
            relatorio_id = salvar_relatorio_mongodb(relatorio_data)
            if relatorio_id:
                st.success("✅ Relatório salvo no banco de dados com sucesso!")
            
            return relatorio_completo
        
    except Exception as e:
        return {
            "partes": [{"titulo": "Erro", "conteudo": f"Erro ao gerar relatório: {str(e)}"}],
            "texto_completo": f"Erro ao gerar relatório: {str(e)}"
        }


        
       

# Interface do usuário ===============================================

# Sessão para armazenar os dados carregados
if 'dados_atual' not in st.session_state:
    st.session_state.dados_atual = None
    st.session_state.dados_anterior = None

# Seção de upload de arquivos e informações do cliente
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

# Seção de informações do cliente
with st.expander("ℹ️ Informações do Cliente (Opcional)"):
    cliente_nome = st.text_input("Nome do Cliente")
    cliente_id = st.text_input("ID do Cliente (se aplicável)")
    cliente_tags = st.text_input("Tags (separadas por vírgula)")
    
    cliente_info = {
        "nome": cliente_nome,
        "id": cliente_id,
        "tags": [tag.strip() for tag in cliente_tags.split(",")] if cliente_tags else []
    }

# Verifica se temos dados para análise
if st.session_state.dados_atual is not None:
    df = st.session_state.dados_atual
    metricas = calcular_metricas(df)
    colunas_numericas = [col for col in metricas.keys()]
    
    with st.sidebar:
        st.header("🔧 Configurações de Análise")
        
        # Seleção de métricas
        metricas_relatorio = st.multiselect(
            "Selecione as métricas para análise",
            options=colunas_numericas,
            default=colunas_numericas[:5] if len(colunas_numericas) > 5 else colunas_numericas
        )
        
        # Tipo de relatório
        tipo_relatorio = st.radio(
            "Tipo de relatório",
            options=["técnico", "gerencial"],
            index=0
        )
        
        # Filtros
        st.subheader("Filtros")
        
        # Adiciona coluna de tipo detectado ao dataframe
        if st.session_state.dados_atual is not None:
            df = st.session_state.dados_atual.copy()
            df['Tipo Detectado'] = df['Campanha'].apply(detectar_tipo_campanha)
            
            # Filtro por tipo detectado
            tipos_detectados = sorted(df['Tipo Detectado'].unique())
            tipos_selecionados = st.multiselect(
                "Tipo de Campanha (detectado pelo nome)",
                options=tipos_detectados,
                default=tipos_detectados
            )
        
        tipo_campanha = st.multiselect(
            "Tipo de Campanha (do relatório)",
            options=df['Tipo de campanha'].unique(),
            default=df['Tipo de campanha'].unique()
        )
        
        status_campanha = st.multiselect(
            "Status da Campanha",
            options=df['Status da campanha'].unique(),
            default=df['Status da campanha'].unique()
        )
        
        mostrar_boxplots = st.checkbox("Mostrar boxplots das métricas")
    
    # Modifica a aplicação dos filtros para incluir o tipo detectado
    df_filtrado = df[
        (df['Tipo Detectado'].isin(tipos_selecionados)) &
        (df['Tipo de campanha'].isin(tipo_campanha)) &
        (df['Status da campanha'].isin(status_campanha))
    ]
    
    # Abas principais
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Visão Geral", "📊 Análise por Métrica", "🔄 Comparativo Mensal", "🧠 Relatório Avançado"])
    
    with tab1:
        st.subheader("Visão Geral das Campanhas - Mês Atual")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Campanhas", len(df_filtrado))
        col2.metric("Campanhas Ativas", len(df_filtrado[df_filtrado['Status da campanha'] == 'Ativa']))
        col3.metric("Campanhas Pausadas", len(df_filtrado[df_filtrado['Status da campanha'] == 'Pausada']))
        
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
            top5 = df_filtrado.nlargest(5, metrica_selecionada)[['Campanha', metrica_selecionada]]
            st.dataframe(top5.style.format({metrica_selecionada: "{:,.2f}"}))
            
            st.subheader("Campanhas abaixo da média")
            bottom5 = df_filtrado.nsmallest(5, metrica_selecionada)[['Campanha', metrica_selecionada]]
            st.dataframe(bottom5.style.format({metrica_selecionada: "{:,.2f}"}))
    
    with tab3:
        st.subheader("Comparativo Mensal")
        
        if st.session_state.dados_anterior is not None:
            # Aplica os mesmos filtros ao mês anterior
            df_anterior_filtrado = st.session_state.dados_anterior[
                (st.session_state.dados_anterior['Tipo de campanha'].isin(tipo_campanha)) &
                (st.session_state.dados_anterior['Status da campanha'].isin(status_campanha))
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
    
    # Na interface do usuário, na parte do relatório (tab4):
    with tab4:
        st.subheader("Relatório Avançado com IA")
        
        if st.button("Gerar Relatório com Análise Avançada"):
            relatorio = gerar_relatorio_llm(
                df_filtrado, 
                metricas, 
                metricas_relatorio, 
                tipo_relatorio, 
                cliente_info,
                st.session_state.dados_anterior if st.session_state.dados_anterior is not None else None
            )
            
            # Exibe cada parte do relatório em seções expansíveis
            for parte in relatorio["partes"]:
                with st.expander(f"**{parte['titulo']}**"):
                    st.markdown(parte["conteudo"])
            
            # Botão para download
            st.download_button(
                label="⬇️ Baixar Relatório Completo",
                data=relatorio["texto_completo"],
                file_name=f"relatorio_{tipo_relatorio}_campanhas.md",
                mime="text/markdown"
            )
            
            # Mostra histórico de relatórios salvos para este cliente (se houver ID)
            if cliente_info.get('id'):
                st.subheader("Histórico de Relatórios")
                relatorios_anteriores = list(collection.find({
                    "cliente.id": cliente_info['id'],
                    "status": "ativo"
                }).sort("data_geracao", -1).limit(5))
                
                if relatorios_anteriores:
                    for rel in relatorios_anteriores:
                        with st.expander(f"Relatório de {rel['data_geracao'].strftime('%d/%m/%Y %H:%M')}"):
                            for parte in rel.get('partes', []):
                                st.markdown(f"**{parte['titulo']}**")
                                st.markdown(parte['conteudo'][:200] + "...")
                else:
                    st.info("Nenhum relatório anterior encontrado para este cliente")
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
