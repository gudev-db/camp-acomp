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
import hashlib
import time
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
import google.generativeai as genai
from typing import Dict, Any
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import tempfile
import base64

# Configuração da página
st.set_page_config(
    layout="wide",
    page_title="Agente Performance",
    page_icon="📊"
)

# CSS personalizado para a aba de planejamento
st.markdown("""
<style>
    .main {
        background-color: #f5f7fa;
    }
    .stTextInput input, .stSelectbox select, .stTextArea textarea {
        border-radius: 8px !important;
        border: 1px solid #d1d5db !important;
    }
    .stButton button {
        background-color: #4f46e5 !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 500 !important;
    }
    .stButton button:hover {
        background-color: #4338ca !important;
    }
    .result-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    table {
        width: 100%;
        border-collapse: collapse;
    }
    th, td {
        padding: 12px;
        text-align: left;
        border-bottom: 1px solid #e5e7eb;
    }
    th {
        background-color: #f9fafb;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        color: #4f46e5 !important;
        font-weight: 600 !important;
    }
    .metric-row {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
    }
    .metric-name {
        width: 200px;
        font-weight: 500;
    }
    .metric-input {
        flex-grow: 1;
    }
    .upload-section {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

rel_metrica = '''
           ###BEGIN RELACAO METRICA VS TIPO DE CAMPANHA###
            Tipo: 📌 Search (Pesquisa) -> Atenção para as métricas:
            *O que é:* Campanhas de busca no Google que aparecem quando usuários pesquisam por termos relacionados.  
            *Objetivos:* Capturar demanda existente, gerar leads/vendas com alta intenção de compra.  
            *Métricas-chave:*
            CTR (Taxa de Cliques) - Principal indicador de relevância do anúncio  
            Conversões - Objetivo final das campanhas de busca  
            CPC médio (Custo por Clique) - Custo da aquisição de tráfego  
            Custo por conversão - Eficiência no ROI  
            IS parte superior pesquisa (Impression Share) - Visibilidade nos melhores posicionamentos  
            Taxa de conversão - Eficácia da landing page  
            
            Tipo: 🎯 Performance Max (Pmax) -> Atenção para as métricas:
            *O que é:* Campanhas automatizadas que usam todos os inventários do Google (YouTube, Display, Search etc.).  
            *Objetivos:* Maximizar conversões com orçamento otimizado automaticamente.  
            *Métricas-chave:*
            Conversões - Métrica principal deste tipo de campanha  
            Custo por conversão - Eficiência de custo  
            CTR - Engajamento com os anúncios  
            Impressões - Alcance da campanha  
            Taxa de conversão - Eficácia do funnel  
            
            Tipo: 📢 Display -> Atenção para as métricas:
            *O que é:* Anúncios visual em sites parceiros do Google.  
            *Objetivos:* Aumentar awareness, remarketing e construção de marca.  
            *Métricas-chave:*
            Impressões - Alcance da campanha  
            CPM médio (Custo por Mil Impressões) - Custo da exposição  
            CTR - Engajamento com os banners  
            Conversões (se for o objetivo)  
            Visualizações (para creatives interativos)  
            
            Tipo: 📹 Video -> Atenção para as métricas:
            *O que é:* Anúncios em formato de vídeo no YouTube e parceiros.  
            *Objetivos:* Engajamento emocional, storytelling de marca e consideração.  
            *Métricas-chave:*
            Visualizações (Views) - Pessoas que assistiram o vídeo  
            CPV médio (Custo por Visualização) - Custo da atenção  
            Engajamentos - Interações com o vídeo  
            Taxa de interação - % de quem interagiu  
            Conversões (se for campanha de conversão)  
            
            Tipo: 🔍 Discovery -> Atenção para as métricas:
            *O que é:* Anúncios nativos no Discover, Gmail e YouTube Home.  
            *Objetivos:* Descobrimento de novos clientes com conteúdo relevante.  
            *Métricas-chave:*
            CTR - Relevância dos anúncios  
            Conversões - Resultados concretos  
            CPC médio - Custo da descoberta  
            Impressões - Alcance orgânico+paid  
            Taxa de conversão - Eficácia pós-clique  
            
            Tipo: 🏷️ Alcance (Reach) -> Atenção para as métricas:
            *O que é:* Campanhas focadas em maximizar alcance único.  
            *Objetivos:* Aumentar awareness de marca com frequência controlada.  
            *Métricas-chave:*
            Impressões - Quantas vezes foi exibido  
            CPM médio - Custo do alcance  
            Frequência (calculada: Impressões/Únicos) - Número médio de visualizações por usuário  
            Engajamentos - Interações com o conteúdo  
            
            Tipo: 📱 Meta (Facebook/Instagram) -> Atenção para as métricas:
            *O que é:* Anúncios no ecossistema Meta (Facebook, Instagram, etc.).  
            *Objetivos:* Varia conforme objetivo da campanha (tráfego, conversões, engajamento, etc.).  
            *Métricas-chave:*
            Resultados - Principal métrica (varia conforme objetivo)  
            Custo por resultado - Eficiência na entrega  
            Alcance - Pessoas únicas que viram o anúncio  
            Impressões - Número total de visualizações  
            CTR (taxa de cliques no link) - Engajamento com o anúncio  
            Frequência - Média de visualizações por pessoa  
            CPM (custo por 1.000 impressões) - Custo de alcance  
            Engajamentos com o post - Interações com o conteúdo  
            ThruPlays - Visualizações completas de vídeos  
            
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

# Conexão com MongoDB
client = MongoClient("mongodb+srv://gustavoromao3345:RqWFPNOJQfInAW1N@cluster0.5iilj.mongodb.net/auto_doc?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE&tlsAllowInvalidCertificates=true")
db = client['arquivos_planejamento']
collection = db['auto_doc']
banco = client["arquivos_planejamento"]
db_clientes = banco["clientes"]
db_usuarios = banco["usuarios"]
db_relatorios = banco["relatorios"]

# Verifica se a API key do Gemini está configurada
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    st.warning("⚠️ Chave da API Gemini não encontrada. O relatório avançado será limitado.")

# =============================================================================
# FUNÇÕES PARA CORREÇÃO DO META
# =============================================================================

def carregar_dados_meta_corrigido(arquivo):
    """Carrega e prepara o arquivo CSV do Meta (Facebook/Instagram) - VERSÃO CORRIGIDA"""
    try:
        # Primeiro, vamos tentar detectar o encoding do arquivo
        df = pd.read_csv(arquivo, encoding='utf-8')
        
        # Se falhar, tentar latin-1
        if df.empty:
            df = pd.read_csv(arquivo, encoding='latin-1')
        
        # Remover linhas completamente vazias
        df = df.dropna(how='all')
        
        # Identificar colunas automaticamente
        colunas_disponiveis = df.columns.tolist()
        
        # Mapeamento dinâmico de colunas
        mapeamento = {}
        for col in colunas_disponiveis:
            col_lower = col.lower()
            
            # Identificar por padrões comuns
            if 'nome da campanha' in col_lower or 'campanha' in col_lower:
                mapeamento[col] = 'Campanha'
            elif 'início dos relatórios' in col_lower or 'inicio dos relatorios' in col_lower or 'data início' in col_lower:
                mapeamento[col] = 'Data início'
            elif 'término dos relatórios' in col_lower or 'termino dos relatorios' in col_lower or 'data término' in col_lower:
                mapeamento[col] = 'Data término'
            elif 'veiculação da campanha' in col_lower or 'veiculacao da campanha' in col_lower or 'status' in col_lower:
                mapeamento[col] = 'Status da campanha'
            elif 'orçamento do conjunto de anúncios' in col_lower or 'orçamento' in col_lower or 'orçamento' in col_lower:
                mapeamento[col] = 'Orçamento'
            elif 'resultados' in col_lower:
                mapeamento[col] = 'Resultados'
            elif 'custo por resultados' in col_lower or 'custo por resultado' in col_lower:
                mapeamento[col] = 'Custo por resultado'
            elif 'valor usado' in col_lower or 'custo' in col_lower or 'gasto' in col_lower:
                mapeamento[col] = 'Custo'
            elif 'alcance' in col_lower:
                mapeamento[col] = 'Alcance'
            elif 'impressões' in col_lower or 'impressoes' in col_lower:
                mapeamento[col] = 'Impressões'
            elif 'ctr' in col_lower or 'taxa de cliques' in col_lower:
                mapeamento[col] = 'CTR'
            elif 'engajamentos' in col_lower or 'engajamento' in col_lower:
                mapeamento[col] = 'Engajamentos'
            elif 'cliques' in col_lower:
                mapeamento[col] = 'Cliques'
            elif 'frequência' in col_lower or 'frequencia' in col_lower:
                mapeamento[col] = 'Frequência'
            elif 'cpm' in col_lower or 'custo por 1000' in col_lower:
                mapeamento[col] = 'CPM'
            elif 'thruplays' in col_lower or 'thruplays' in col_lower:
                mapeamento[col] = 'ThruPlays'
            elif 'visualizações' in col_lower or 'visualizacoes' in col_lower:
                mapeamento[col] = 'Visualização'
        
        # Renomear colunas
        df = df.rename(columns=mapeamento)
        
        # Colunas numéricas padrão
        colunas_numericas = [
            'Orçamento', 'Resultados', 'Alcance', 'Impressões', 
            'Custo por resultado', 'Custo', 'CTR', 'Engajamentos',
            'Cliques', 'Frequência', 'CPM', 'Visualização', 'ThruPlays'
        ]
        
        # Converter colunas numéricas
        for col in colunas_numericas:
            if col in df.columns:
                # Remover caracteres não numéricos
                df[col] = df[col].astype(str).str.replace(',', '.').str.replace('%', '').str.replace('R$', '').str.replace('$', '').str.replace(' ', '')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Adicionar coluna para identificar a plataforma
        df['Plataforma'] = 'Meta'
        
        # Log para debug
        st.success(f"✅ Dados do Meta carregados: {len(df)} linhas, {len(df.columns)} colunas")
        st.info(f"Colunas disponíveis: {', '.join(df.columns.tolist())}")
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar arquivo do Meta: {str(e)}")
        return None

# =============================================================================
# FUNÇÕES PARA UPLOAD UNIFICADO
# =============================================================================

def criar_interface_upload_unificado():
    """Cria interface unificada para upload de relatórios"""
    st.markdown("### 📁 Upload Unificado de Relatórios")
    
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📅 Mês Atual")
            uploaded_files_atual = st.file_uploader(
                "Faça upload dos relatórios do mês atual",
                type=["csv", "xlsx"],
                accept_multiple_files=True,
                key="upload_atual"
            )
            
            if uploaded_files_atual:
                st.success(f"✅ {len(uploaded_files_atual)} arquivo(s) do mês atual carregado(s)")
                
                for file in uploaded_files_atual:
                    # Detectar tipo de arquivo
                    if 'google' in file.name.lower() or 'ads' in file.name.lower():
                        plataforma = 'Google Ads'
                    elif 'meta' in file.name.lower() or 'facebook' in file.name.lower() or 'instagram' in file.name.lower():
                        plataforma = 'Meta'
                    else:
                        plataforma = 'Desconhecido'
                    
                    st.info(f"📄 {file.name} - {plataforma}")
        
        with col2:
            st.markdown("#### 🗓️ Mês Anterior")
            uploaded_files_anterior = st.file_uploader(
                "Faça upload dos relatórios do mês anterior",
                type=["csv", "xlsx"],
                accept_multiple_files=True,
                key="upload_anterior"
            )
            
            if uploaded_files_anterior:
                st.success(f"✅ {len(uploaded_files_anterior)} arquivo(s) do mês anterior carregado(s)")
                
                for file in uploaded_files_anterior:
                    if 'google' in file.name.lower() or 'ads' in file.name.lower():
                        plataforma = 'Google Ads'
                    elif 'meta' in file.name.lower() or 'facebook' in file.name.lower() or 'instagram' in file.name.lower():
                        plataforma = 'Meta'
                    else:
                        plataforma = 'Desconhecido'
                    
                    st.info(f"📄 {file.name} - {plataforma}")
    
    # Processar os arquivos
    dados_atual = {}
    dados_anterior = {}
    
    if uploaded_files_atual:
        for file in uploaded_files_atual:
            try:
                if 'google' in file.name.lower() or 'ads' in file.name.lower():
                    df = carregar_dados_google_ads(file)
                    if df is not None:
                        dados_atual['Google Ads'] = df
                elif 'meta' in file.name.lower() or 'facebook' in file.name.lower() or 'instagram' in file.name.lower():
                    df = carregar_dados_meta_corrigido(file)
                    if df is not None:
                        dados_atual['Meta'] = df
            except Exception as e:
                st.error(f"Erro ao processar {file.name}: {str(e)}")
    
    if uploaded_files_anterior:
        for file in uploaded_files_anterior:
            try:
                if 'google' in file.name.lower() or 'ads' in file.name.lower():
                    df = carregar_dados_google_ads(file)
                    if df is not None:
                        dados_anterior['Google Ads'] = df
                elif 'meta' in file.name.lower() or 'facebook' in file.name.lower() or 'instagram' in file.name.lower():
                    df = carregar_dados_meta_corrigido(file)
                    if df is not None:
                        dados_anterior['Meta'] = df
            except Exception as e:
                st.error(f"Erro ao processar {file.name}: {str(e)}")
    
    return dados_atual, dados_anterior

# =============================================================================
# FUNÇÕES PARA ANÁLISE CAMPANHA A CAMPANHA
# =============================================================================

def analise_campanha_a_campanha(dados_atual, dados_anterior):
    """Realiza análise detalhada campanha a campanha comparando meses"""
    
    if not dados_atual:
        st.warning("Nenhum dado do mês atual disponível para análise")
        return None
    
    st.markdown("## 📊 Análise Detalhada Campanha a Campanha")
    
    # Criar abas para cada plataforma
    plataformas = list(dados_atual.keys())
    tabs = st.tabs([f"📱 {p}" for p in plataformas])
    
    resultados_por_plataforma = {}
    
    for i, plataforma in enumerate(plataformas):
        with tabs[i]:
            df_atual = dados_atual.get(plataforma)
            df_anterior = dados_anterior.get(plataforma) if dados_anterior else None
            
            if df_atual is None:
                st.warning(f"Nenhum dado disponível para {plataforma}")
                continue
            
            # Selecionar campanhas para análise
            campanhas_disponiveis = sorted(df_atual['Campanha'].unique())
            
            col1, col2 = st.columns([2, 1])
            with col1:
                campanha_selecionada = st.selectbox(
                    f"Selecione a campanha para análise detalhada ({plataforma})",
                    options=campanhas_disponiveis,
                    key=f"campanha_{plataforma}"
                )
            
            with col2:
                st.metric("Total de Campanhas", len(campanhas_disponiveis))
            
            # Filtrar dados da campanha selecionada
            dados_campanha_atual = df_atual[df_atual['Campanha'] == campanha_selecionada]
            
            if df_anterior is not None:
                dados_campanha_anterior = df_anterior[df_anterior['Campanha'] == campanha_selecionada]
            else:
                dados_campanha_anterior = None
            
            # Mostrar métricas principais
            st.subheader(f"📈 Métricas da Campanha: {campanha_selecionada}")
            
            # Identificar métricas disponíveis
            metricas_disponiveis = []
            colunas_numericas = dados_campanha_atual.select_dtypes(include=[np.number]).columns.tolist()
            metricas_importantes = ['Custo', 'Impressões', 'Cliques', 'Conversões', 'Resultados', 
                                   'CTR', 'CPC médio', 'Custo por conversão', 'Alcance', 'Engajamentos']
            
            for metrica in metricas_importantes:
                if metrica in colunas_numericas:
                    metricas_disponiveis.append(metrica)
            
            # Adicionar outras métricas numéricas
            for col in colunas_numericas:
                if col not in metricas_disponiveis and col in colunas_numericas:
                    metricas_disponiveis.append(col)
            
            # Comparação mês a mês
            if dados_campanha_anterior is not None and not dados_campanha_anterior.empty:
                st.subheader("🔄 Comparação Mês a Mês")
                
                # Criar DataFrame comparativo
                dados_comparativos = []
                
                for metrica in metricas_disponiveis[:10]:  # Limitar a 10 métricas para não sobrecarregar
                    valor_atual = dados_campanha_atual[metrica].sum() if not dados_campanha_atual.empty else 0
                    valor_anterior = dados_campanha_anterior[metrica].sum() if not dados_campanha_anterior.empty else 0
                    
                    if valor_anterior != 0:
                        variacao = ((valor_atual - valor_anterior) / valor_anterior) * 100
                    else:
                        variacao = 0 if valor_atual == 0 else 100
                    
                    dados_comparativos.append({
                        'Métrica': metrica,
                        'Mês Atual': valor_atual,
                        'Mês Anterior': valor_anterior,
                        'Variação %': variacao,
                        'Tendência': '📈' if variacao > 0 else '📉' if variacao < 0 else '➡️'
                    })
                
                df_comparativo = pd.DataFrame(dados_comparativos)
                
                # Formatação dos valores
                def formatar_valor(val):
                    if isinstance(val, (int, float)):
                        if abs(val) >= 1000000:
                            return f"R$ {val/1000000:.1f}M"
                        elif abs(val) >= 1000:
                            return f"R$ {val/1000:.1f}K"
                        else:
                            return f"R$ {val:.2f}"
                    return val
                
                # Mostrar tabela comparativa
                st.dataframe(
                    df_comparativo.style.format({
                        'Mês Atual': '{:.2f}',
                        'Mês Anterior': '{:.2f}',
                        'Variação %': '{:.1f}%'
                    }).apply(
                        lambda x: ['background-color: #e6ffe6' if x['Variação %'] > 0 else 
                                 'background-color: #ffe6e6' if x['Variação %'] < 0 else '' 
                                 for i in range(len(x))], 
                        axis=1
                    ),
                    use_container_width=True
                )
                
                # Gráfico de comparação
                st.subheader("📊 Evolução das Principais Métricas")
                
                metricas_grafico = st.multiselect(
                    f"Selecione métricas para o gráfico ({plataforma})",
                    options=metricas_disponiveis,
                    default=metricas_disponiveis[:3] if len(metricas_disponiveis) >= 3 else metricas_disponiveis,
                    key=f"metricas_grafico_{plataforma}"
                )
                
                if metricas_grafico:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    meses = ['Mês Anterior', 'Mês Atual']
                    
                    for metrica in metricas_grafico:
                        valores = [
                            dados_campanha_anterior[metrica].sum() if not dados_campanha_anterior.empty else 0,
                            dados_campanha_atual[metrica].sum() if not dados_campanha_atual.empty else 0
                        ]
                        ax.plot(meses, valores, marker='o', label=metrica)
                    
                    ax.set_title(f'Evolução das Métricas: {campanha_selecionada}')
                    ax.set_ylabel('Valor')
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    
                    st.pyplot(fig)
            
            else:
                st.info("ℹ️ Apenas dados do mês atual disponíveis para esta campanha")
                
                # Mostrar métricas atuais
                colunas_mostrar = ['Campanha'] + metricas_disponiveis[:8]
                st.dataframe(dados_campanha_atual[colunas_mostrar], use_container_width=True)
            
            # Armazenar resultados para esta plataforma
            resultados_por_plataforma[plataforma] = {
                'campanha': campanha_selecionada,
                'dados_atual': dados_campanha_atual,
                'dados_anterior': dados_campanha_anterior
            }
    
    return resultados_por_plataforma

# =============================================================================
# FUNÇÕES PARA GERAÇÃO DE RELATÓRIO EM PPT (PDF)
# =============================================================================

def gerar_relatorio_pdf(dados_atual, dados_anterior, cliente_info=None):
    """Gera um relatório em PDF com análise comparativa"""
    
    buffer = io.BytesIO()
    
    # Criar documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Título do relatório
    titulo = Paragraph(f"Relatório Mensal de Performance", styles['Title'])
    elements.append(titulo)
    elements.append(Spacer(1, 12))
    
    # Informações do cliente
    if cliente_info and cliente_info.get('nome'):
        cliente_text = f"Cliente: {cliente_info['nome']}"
        if cliente_info.get('id'):
            cliente_text += f" | ID: {cliente_info['id']}"
        elements.append(Paragraph(cliente_text, styles['Normal']))
    
    data_relatorio = Paragraph(f"Período: {datetime.now().strftime('%B/%Y')} vs {datetime.now().replace(month=datetime.now().month-1).strftime('%B/%Y') if datetime.now().month > 1 else 'Dezembro/%s' % (datetime.now().year-1)}", styles['Normal'])
    elements.append(data_relatorio)
    elements.append(Spacer(1, 24))
    
    # Resumo executivo
    elements.append(Paragraph("Resumo Executivo", styles['Heading2']))
    resumo_text = """
    Este relatório apresenta uma análise comparativa do desempenho das campanhas de marketing digital 
    entre o mês atual e o mês anterior. Foram analisadas métricas chave de performance, incluindo 
    custos, impressões, cliques, conversões e engajamento.
    """
    elements.append(Paragraph(resumo_text, styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Análise por plataforma
    elements.append(Paragraph("Análise por Plataforma", styles['Heading2']))
    
    for plataforma, df in dados_atual.items():
        elements.append(Paragraph(f"Plataforma: {plataforma}", styles['Heading3']))
        
        # Estatísticas básicas
        stats_text = f"""
        Total de Campanhas: {len(df['Campanha'].unique())}
        Campanhas Ativas: {len(df[df['Status da campanha'] == 'Ativada'] if 'Status da campanha' in df.columns else df)}
        """
        elements.append(Paragraph(stats_text, styles['Normal']))
        
        # Tabela de métricas principais
        if 'Custo' in df.columns:
            custo_total = df['Custo'].sum()
            if dados_anterior and plataforma in dados_anterior:
                custo_anterior = dados_anterior[plataforma]['Custo'].sum()
                variacao = ((custo_total - custo_anterior) / custo_anterior * 100) if custo_anterior != 0 else 0
            else:
                variacao = 0
            
            # Criar tabela simples
            data = [
                ['Métrica', 'Mês Atual', 'Mês Anterior', 'Variação'],
                ['Custo Total', f"R$ {custo_total:.2f}", 
                 f"R$ {custo_anterior:.2f}" if dados_anterior and plataforma in dados_anterior else 'N/A',
                 f"{variacao:.1f}%"]
            ]
            
            # Adicionar mais métricas se disponíveis
            for metrica in ['Impressões', 'Cliques', 'Conversões']:
                if metrica in df.columns:
                    valor_atual = df[metrica].sum()
                    if dados_anterior and plataforma in dados_anterior and metrica in dados_anterior[plataforma].columns:
                        valor_anterior = dados_anterior[plataforma][metrica].sum()
                        variacao_metrica = ((valor_atual - valor_anterior) / valor_anterior * 100) if valor_anterior != 0 else 0
                    else:
                        valor_anterior = 0
                        variacao_metrica = 0
                    
                    data.append([
                        metrica,
                        f"{valor_atual:,.0f}",
                        f"{valor_anterior:,.0f}" if valor_anterior != 0 else 'N/A',
                        f"{variacao_metrica:.1f}%"
                    ])
            
            # Criar tabela
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 12))
    
    # Recomendações
    elements.append(Paragraph("Recomendações", styles['Heading2']))
    recomendacoes_text = """
    1. Revisar campanhas com baixo CTR e alto custo
    2. Aumentar investimento em campanhas com melhor ROI
    3. Otimizar criativos para melhor engajamento
    4. Ajustar targeting para melhorar relevância
    5. Monitorar campanhas de remarketing
    """
    elements.append(Paragraph(recomendacoes_text, styles['Normal']))
    
    # Rodapé
    elements.append(Spacer(1, 24))
    data_geracao = Paragraph(f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Italic'])
    elements.append(data_geracao)
    
    # Construir PDF
    doc.build(elements)
    
    buffer.seek(0)
    return buffer

# =============================================================================
# FUNÇÕES EXISTENTES DO APLICATIVO (MANTIDAS)
# =============================================================================

# Configurações do aplicativo
METRICAS_POR_ETAPA_PLANEJAMENTO = {
    'Topo': ['Impressões', 'Alcance', 'Custo', 'CPM', 'Cliques', 'CTR', 'Engajamentos', 'Frequência'],
    'Meio': ['Impressões', 'Cliques', 'CTR', 'CPM', 'Custo', 'Engajamentos', 'Visualizações', 'ThruPlays'],
    'Fundo': ['Impressões', 'Cliques', 'Resultados', 'CTR', 'CPM', 'Custo por resultado', 'Custo']
}

DESCRICOES_METRICAS = {
    'Impressões': "Número total de vezes que seu anúncio foi exibido",
    'Alcance': "Número de pessoas únicas que viram seu anúncio",
    'Custo': "Custo total da campanha",
    'CPM': "Custo por mil impressões",
    'Cliques': "Número total de cliques no anúncio",
    'CTR': "Taxa de cliques (cliques/impressões)",
    'Engajamentos': "Interações com o anúncio (curtidas, comentários, compartilhamentos)",
    'Frequência': "Média de vezes que cada pessoa viu seu anúncio",
    'Visualizações': "Visualizações do vídeo (3s ou mais)",
    'ThruPlays': "Visualizações completas do vídeo",
    'Resultados': "Número de conversões (compras, cadastros, etc.)",
    'Custo por resultado': "Custo médio por conversão",
}

# Inicializar Gemini para planejamento
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
    modelo_texto = genai.GenerativeModel("gemini-1.5-flash")

def detectar_tipo_campanha(nome_campanha):
    """Detecta o tipo de campanha com base no nome"""
    try:
        if pd.isna(nome_campanha) or not isinstance(nome_campanha, str):
            return 'Outros'
            
        nome = nome_campanha.lower()
        
        if 'search' in nome or 'pesquisa' in nome:
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
        elif 'meta' in nome or 'facebook' in nome or 'instagram' in nome or 'social' in nome:
            return 'Meta'
        else:
            return 'Outros'
    except Exception as e:
        print(f"Erro ao detectar tipo de campanha: {str(e)}")
        return 'Outros'

def carregar_dados_google_ads(arquivo):
    """Carrega e prepara o arquivo CSV do Google Ads"""
    try:
        df = pd.read_csv(arquivo, skiprows=2, encoding='utf-8')
        df = df.dropna(how='all')
        
        mapeamento_colunas = {
            'Status da campanha': 'Status da campanha',
            'Campanha': 'Campanha',
            'Nome do orÃ§amento': 'Nome do orçamento',
            'CÃ³digo da moeda': 'Código da moeda',
            'OrÃ§amento': 'Orçamento',
            'Tipo de orÃ§amento': 'Tipo de orçamento',
            'Status': 'Status',
            'Motivos do status': 'Motivos do status',
            'PontuaÃ§Ã£o de otimizaÃ§Ã£o': 'Pontuação de otimização',
            'Tipo de campanha': 'Tipo de campanha',
            'CPV mÃ©dio': 'CPV médio',
            'InteraÃ§Ãµes': 'Interações',
            'Taxa de interaÃ§Ã£o': 'Taxa de interação',
            'Custo': 'Custo',
            'Impr.': 'Impressões',
            'Cliques': 'Cliques',
            'ConversÃµes': 'Conversões',
            'CTR': 'CTR',
            'CPM mÃ©dio': 'CPM médio',
            'CPC mÃ©d.': 'CPC médio',
            'Custo / conv.': 'Custo por conversão',
            'Custo mÃ©dio': 'Custo médio',
            'Engajamentos': 'Engajamentos',
            'IS parte sup. pesq.': 'IS parte superior pesquisa',
            'IS 1Âª posiÃ§Ã£o pesq.': 'IS 1ª posição pesquisa',
            'VisualizaÃ§Ãµes': 'Visualizações',
            'Tipo de estratÃ©gia de lances': 'Tipo de estratégia de lances',
            'Taxa de conv.': 'Taxa de conversão'
        }
        
        df = df.rename(columns=mapeamento_colunas)
        
        colunas_numericas = [
            'CPV médio', 'Interações', 'Taxa de interação', 'Custo', 'Impressões',
            'Cliques', 'Conversões', 'CTR', 'CPM médio', 'CPC médio', 
            'Custo por conversão', 'Custo médio', 'Engajamentos',
            'IS parte superior pesquisa', 'IS 1ª posição pesquisa', 'Visualizações',
            'Taxa de conversão'
        ]
        
        for col in colunas_numericas:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '.').str.replace('%', '').str.replace(' ', '')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Adicionar coluna para identificar a plataforma
        df['Plataforma'] = 'Google Ads'
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar arquivo do Google Ads: {str(e)}")
        return None

def combinar_dados_plataformas(df_google_ads, df_meta):
    """Combina dados de Google Ads e Meta em um único DataFrame"""
    try:
        # Verificar se temos dados de ambas as plataformas
        dfs = []
        
        if df_google_ads is not None and not df_google_ads.empty:
            dfs.append(df_google_ads)
        
        if df_meta is not None and not df_meta.empty:
            dfs.append(df_meta)
        
        if not dfs:
            return None
        
        # Combinar os DataFrames
        df_combinado = pd.concat(dfs, ignore_index=True)
        
        # Padronizar colunas comuns
        colunas_comuns = ['Campanha', 'Status da campanha', 'Orçamento', 'Custo', 'Impressões', 
                         'Cliques', 'CTR', 'Plataforma']
        
        # Adicionar colunas específicas de cada plataforma com valores padrão
        colunas_google = ['Conversões', 'CPC médio', 'Custo por conversão', 'CPM médio']
        colunas_meta = ['Resultados', 'Custo por resultado', 'Alcance', 'Frequência', 'CPM']
        
        for col in colunas_google:
            if col not in df_combinado.columns:
                df_combinado[col] = np.nan
        
        for col in colunas_meta:
            if col not in df_combinado.columns:
                df_combinado[col] = np.nan
        
        # Adicionar colunas de tipo detectado e etapa do funil
        df_combinado['Tipo Detectado'] = df_combinado['Campanha'].apply(detectar_tipo_campanha)
        df_combinado['Etapa Funil'] = df_combinado['Campanha'].apply(detectar_etapa_funil)
        
        return df_combinado
        
    except Exception as e:
        st.error(f"Erro ao combinar dados: {str(e)}")
        return None

def detectar_etapa_funil(nome_campanha):
    """Detecta a etapa do funil com base no nome da campanha"""
    try:
        if pd.isna(nome_campanha) or not isinstance(nome_campanha, str):
            return 'Outros'
            
        nome = nome_campanha.lower()
        
        topo_keywords = ['awareness', 'consciencia', 'alcance', 'reach', 'branding', 'marca', 'reconhecimento']
        meio_keywords = ['consideracao', 'consideração', 'consideration', 'engajamento', 'engagement', 'video', 'vídeo', 'traffic', 'tráfego']
        fundo_keywords = ['conversao', 'conversão', 'conversion', 'venda', 'sales', 'lead', 'performance', 'pmax', 'contato']
        
        if any(keyword in nome for keyword in topo_keywords):
            return 'Topo'
        elif any(keyword in nome for keyword in meio_keywords):
            return 'Meio'
        elif any(keyword in nome for keyword in fundo_keywords):
            return 'Fundo'
        else:
            return 'Outros'
    except Exception as e:
        print(f"Erro ao detectar etapa do funil: {str(e)}")
        return 'Outros'

METRICAS_POR_ETAPA = {
    'Topo': ['Impressões', 'Alcance', 'Custo', 'CPM', 'Cliques', 'CTR', 'Engajamentos', 'Frequência'],
    'Meio': ['Impressões', 'Cliques', 'CTR', 'CPM', 'Custo', 'Engajamentos', 'Visualização', 'ThruPlays'],
    'Fundo': ['Impressões', 'Cliques', 'Resultados', 'Conversões', 'CTR', 'CPM', 'Custo por resultado', 'Custo por conversão', 'Custo']
}

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
    """Cria a boxplot para uma coluna numérica"""
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
        
        valores = {
            'Mês Atual': dados_atual[metrica].mean(),
            'Mês Anterior': dados_anterior[metrica].mean()
        }
        
        variacao = ((valores['Mês Atual'] - valores['Mês Anterior']) / valores['Mês Anterior']) * 100
        
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

def criar_usuario(email, senha, nome):
    """Cria um novo usuário no banco de dados"""
    if db_usuarios.find_one({"email": email}):
        return False, "Usuário já existe"
    
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    
    novo_usuario = {
        "email": email,
        "senha": senha_hash,
        "nome": nome,
        "data_criacao": datetime.now(),
        "ultimo_login": None,
        "ativo": True
    }
    
    try:
        db_usuarios.insert_one(novo_usuario)
        return True, "Usuário criado com sucesso"
    except Exception as e:
        return False, f"Erro ao criar usuário: {str(e)}"

def verificar_login(email, senha):
    """Verifica as credenciais do usuário"""
    usuario = db_usuarios.find_one({"email": email})
    
    if not usuario:
        return False, None, "Usuário não encontrado"
    
    if not usuario.get("ativo", True):
        return False, None, "Usuário desativado"
    
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    
    if usuario["senha"] == senha_hash:
        db_usuarios.update_one(
            {"_id": usuario["_id"]},
            {"$set": {"ultimo_login": datetime.now()}}
        )
        return True, usuario, "Login bem-sucedido"
    else:
        return False, None, "Senha incorreta"

def salvar_relatorio_mongodb(relatorio_data, usuario_id=None):
    """Salva o relatório no MongoDB"""
    try:
        if usuario_id:
            relatorio_data["usuario_id"] = usuario_id
        
        result = db_relatorios.insert_one(relatorio_data)
        return str(result.inserted_id)
    except Exception as e:
        st.error(f"Erro ao salvar no MongoDB: {str(e)}")
        return None

def obter_relatorios_usuario(usuario_id, limite=10):
    """Obtém os relatórios de um usuário específico"""
    try:
        relatorios = list(db_relatorios.find(
            {"usuario_id": usuario_id},
            {"titulo": 1, "data_geracao": 1, "tipo": 1, "cliente.nome": 1, "plataformas": 1}
        ).sort("data_geracao", -1).limit(limite))
        
        return relatorios
    except Exception as e:
        st.error(f"Erro ao buscar relatórios: {str(e)}")
        return []

def obter_relatorio_completo(relatorio_id):
    """Obtém um relatório completo pelo ID"""
    try:
        relatorio = db_relatorios.find_one({"_id": ObjectId(relatorio_id)})
        return relatorio
    except Exception as e:
        st.error(f"Erro ao buscar relatório: {str(e)}")
        return None

def gerar_nome_relatorio(cliente_info, plataformas, tipo_relatorio):
    """Gera um nome descritivo para o relatório incluindo cliente e plataformas"""
    nome_cliente = cliente_info.get('nome', 'ClienteNaoEspecificado').replace(' ', '_')
    
    # Formatar plataformas
    if plataformas:
        plataformas_str = '_'.join(plataformas).replace(' ', '')
    else:
        plataformas_str = 'PlataformaNaoEspecificada'
    
    # Formatar tipo de relatório
    tipo_str = 'tecnico' if tipo_relatorio == 'técnico' else 'gerencial'
    
    # Data atual
    data_str = datetime.now().strftime('%Y%m%d_%H%M')
    
    return f"relatorio_{nome_cliente}_{plataformas_str}_{tipo_str}_{data_str}"

def gerar_recomendacao_estrategica(params: Dict[str, Any]) -> str:
    """Gera a recomendação estratégica inicial"""
    etapa_funil = params['etapa_funil']
    okrs_escolhidos = [k for k, v in params['metricas'].items() if v['selecionada']]
    metas_especificas = [f"{k}: {v['valor']}" for k, v in params['metricas'].items() if v['selecionada'] and v['valor']]

    prompt = f"""
    Como especialista em planejamento de mídia digital, analise os seguintes parâmetros e forneça uma recomendação estratégica:

    **Campanha:** {params['objetivo_campanha']} (Etapa do Funil: {etapa_funil})
    **Tipo de Campanha:** {params['tipo_campanha']}
    **Budget Total:** R$ {params['budget']:,.2f}
    **Período da Campanha:** {params['periodo']}
    **Ferramentas/Plataformas:** {", ".join(params['ferramentas'])}
    **Localização Primária:** {params['localizacao_primaria']}
    **Localização Secundária:** {params['localizacao_secundaria']}
    **Tipo de Público:** {params['tipo_publico']}
    **Tipos de Criativo:** {", ".join(params['tipo_criativo'])}
    **OKRs Escolhidos:** {", ".join(okrs_escolhidos) if okrs_escolhidos else "A serem definidos"}
    **Metas Específicas:** {", ".join(metas_especificas) if metas_especificas else "Nenhuma meta específica"}
    **Detalhes da Ação:** {params['detalhes_acao'] or "Nenhum"}
    **Observações:** {params['observacoes'] or "Nenhuma"}

    Forneça:
    1. Análise estratégica focada em {etapa_funil} do funil (150-200 palavras)
    2. Principais oportunidades para os OKRs selecionados
    3. Riscos potenciais específicos para esta etapa
    4. Recomendação geral de abordagem

    Dicas:
    - Mantenha o foco absoluto nos OKRs selecionados: {", ".join(okrs_escolhidos) if okrs_escolhidos else "gerar sugestões apropriadas"}
    - Considere as metas específicas quando fornecidas
    - Adapte ao período especificado

    Formato: Markdown com headers (##, ###)
    """
    
    if gemini_api_key:
        response = modelo_texto.generate_content(prompt)
        return response.text
    else:
        return "**API do Gemini não configurada.** Configure a chave da API para usar esta funcionalidade."

def gerar_distribuicao_budget(params: Dict[str, Any], recomendacao_estrategica: str) -> str:
    """Gera a distribuição de budget baseada na recomendação estratégica"""
    etapa_funil = params['etapa_funil']
    okrs_escolhidos = [k for k, v in params['metricas'].items() if v['selecionada']]
    metas_especificas = [f"{k}: {v['valor']}" for k, v in params['metricas'].items() if v['selecionada'] and v['valor']]

    prompt = f"""
    Com base na seguinte recomendação estratégica (Etapa {etapa_funil} do Funil):
    {recomendacao_estrategica}

    E nos parâmetros originais:
    - Budget: R$ {params['budget']:,.2f}
    - Período: {params['periodo']}
    - Plataformas: {", ".join(params['ferramentas'])}
    - Localizações: Primária ({params['localizacao_primaria']}), Secundária ({params['localizacao_secundaria']})
    - Tipos de Criativo: {", ".join(params['tipo_criativo'])}
    - OKRs: {", ".join(okrs_escolhidos) if okrs_escolhidos else "A serem otimizados"}
    - Metas: {", ".join(metas_especificas) if metas_especificas else "Nenhuma específica"}

    Crie uma tabela detalhada de distribuição de budget OTIMIZADA PARA OS OKRs SELECIONADOS com:
    1. Divisão por plataforma (% e valor)
    2. Alocação geográfica (primária vs secundária)
    3. Tipos de criativos recomendados (APENAS: {", ".join(params['tipo_criativo'])})
    4. Justificativa estratégica para cada alocação

    REGRAS:
    - Priorize os OKRs selecionados: {", ".join(okrs_escolhidos) if okrs_escolhidos else "otimize para a etapa do funil"}
    - Considere as metas específicas quando fornecidas
    - Não sugerir criativos fora dos tipos especificados
    - Manter foco absoluto nos estados solicitados

    Inclua também uma breve análise (50-100 palavras) explicando como a distribuição atende aos objetivos.

    Formato: Markdown com tabelas (use | para divisão)
    """
    
    if gemini_api_key:
        response = modelo_texto.generate_content(prompt)
        return response.text
    else:
        return "**API do Gemini não configurada.** Configure a chave da API para usar esta funcionalidade."

def gerar_previsao_resultados(params: Dict[str, Any], recomendacao_estrategica: str, distribuicao_budget: str) -> str:
    """Gera previsão de resultados baseada nos parâmetros"""
    etapa_funil = params['etapa_funil']
    okrs_escolhidos = [k for k, v in params['metricas'].items() if v['selecionada']]
    metas_especificas = [f"{k}: {v['valor']}" for k, v in params['metricas'].items() if v['selecionada'] and v['valor']]

    prompt = f"""
    Com base na estratégia para {etapa_funil} do funil:
    {recomendacao_estrategica}

    E na distribuição de budget:
    {distribuicao_budget}

    Estime os resultados ESPERADOS considerando:
    - Budget total: R$ {params['budget']:,.2f}
    - Período: {params['periodo']}
    - OKRs: {", ".join(okrs_escolhidos) if okrs_escolhidos else "A serem otimizados"}
    - Metas: {", ".join(metas_especificas) if metas_especificas else "Nenhuma específica"}

    Forneça:
    1. Tabela com métricas ESPECÍFICAS para os OKRs selecionados
    2. Estimativas realistas baseadas em benchmarks
    3. Análise de potencial desempenho (50-100 palavras)
    4. KPIs CHAVE para monitorar

    DICAS:
    - Destaque os OKRs selecionados: {", ".join(okrs_escolhidos) if okrs_escolhidos else "foco na etapa do funil"}
    - Considere as metas específicas quando fornecidas
    - Use benchmarks realistas para o setior

    Formato: Markdown com tabelas
    """
    
    if gemini_api_key:
        response = modelo_texto.generate_content(prompt)
        return response.text
    else:
        return "**API do Gemini não configurada.** Configure a chave da API para usar esta funcionalidade."

def gerar_recomendacoes_publico(params: Dict[str, Any], recomendacao_estrategica: str) -> str:
    """Gera recomendações detalhadas de público-alvo"""
    etapa_funil = params['etapa_funil']
    okrs_escolhidos = [k for k, v in params['metricas'].items() if v['selecionada']]

    prompt = f"""
    Para a campanha na etapa {etapa_funil} do funil com:
    - Tipo de Público: {params['tipo_publico']}
    - Objetivo: {params['objetivo_campanha']}
    - Plataformas: {", ".join(params['ferramentas'])}
    - Localizações: {params['localizacao_primaria']} (primária), {params['localizacao_secundaria']} (secundária)
    - OKRs: {", ".join(okrs_escolhidos) if okrs_escolhidos else "A serem otimizados"}

    E considerando a estratégia geral:
    {recomendacao_estrategica}

    Desenvolva recomendações de público OTIMIZADAS PARA OS OBJETIVOS incluindo:
    1. Segmentação específica para os OKRs selecionados
    2. Parâmetros de targeting focados nos objetivos
    3. Estratégias de expansão adequadas
    4. Considerações sobre frequência e saturação

    REGRAS:
    - Manter foco absoluto nos estados especificados
    - Adaptar recomendações aos OKRs selecionados
    - Priorizar estratégias adequadas para a etapa {etapa_funil}

    Formato: Markdown com listas e headers
    """
    
    if gemini_api_key:
        response = modelo_texto.generate_content(prompt)
        return response.text
    else:
        return "**API do Gemini não configurada.** Configure a chave da API para usar esta funcionalidade."

def gerar_cronograma(params: Dict[str, Any], recomendacao_estrategica: str, distribuicao_budget: str) -> str:
    """Gera cronograma de implementação"""
    etapa_funil = params['etapa_funil']
    okrs_escolhidos = [k for k, v in params['metricas'].items() if v['selecionada']]

    prompt = f"""
    Com base na estratégia para {etapa_funil} do funil:
    {recomendacao_estrategica}

    E na distribuição de budget:
    {distribuicao_budget}

    Crie um cronograma OTIMIZADO considerando:
    - Budget total: R$ {params['budget']:,.2f}
    - Período: {params['periodo']}
    - Plataformas: {", ".join(params['ferramentas'])}
    - OKRs: {", ".join(okrs_escolhidos) if okrs_escolhidos else "A serem otimizados"}

    Inclua:
    1. Fases de implementação adequadas
    2. Distribuição temporal do budget
    3. Marcos importantes
    4. Frequência de ajustes recomendada

    DICAS:
    - Adaptar cronograma aos objetivos específicos
    - Não incluir fases irrelevantes
    - Manter realismo no período especificado

    Formato: Markdown com tabelas ou listas numeradas
    """
    
    if gemini_api_key:
        response = modelo_texto.generate_content(prompt)
        return response.text
    else:
        return "**API do Gemini não configurada.** Configure a chave da API para usar esta funcionalidade."

def mostrar_planejamento_midia():
    """Mostra a aba de planejamento de mídia"""
    st.title("📊 IA para Planejamento de Mídia")
    st.markdown("""
    **Crie planos de mídia otimizados com alocação automática de verba por estratégia, plataforma e localização.**
    """)

    # Estado da sessão para planejamento
    if 'plano_completo' not in st.session_state:
        st.session_state.plano_completo = {}
    if 'current_step_planejamento' not in st.session_state:
        st.session_state.current_step_planejamento = 0

    # Abas principais do planejamento
    tab1, tab2 = st.tabs(["📋 Criar Novo Plano", "📊 Exemplos por Etapa"])

    with tab1:
        st.header("Informações do Plano de Mídia")
        
        with st.form("plano_midia_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                objetivo_campanha = st.text_input(
                    "Nome/Objetivo da Campanha*",
                    placeholder="Ex: Campanha de Awareness - Marca X",
                    value="Campanha de Awareness - Marca X"
                )
                
                tipo_campanha = st.selectbox(
                    "Tipo de Campanha*",
                    ["Alcance", "Engajamento", "Tráfego", "Conversão"],
                    index=0
                )
                
                etapa_funil = st.selectbox(
                    "Etapa do Funil*",
                    ["Topo", "Meio", "Fundo"],
                    index=0,
                    help="Topo: Conscientização | Meio: Consideração | Fundo: Conversão"
                )
                
                budget = st.number_input(
                    "Budget Total (R$)*",
                    min_value=1000,
                    value=100000,
                    step=1000
                )
                
                periodo = st.selectbox(
                    "Período da Campanha*",
                    ["1 mês", "2 meses", "3 meses", "6 meses", "1 ano"],
                    index=0
                )
                
            with col2:
                ferramentas = st.multiselect(
                    "Ferramentas/Plataformas*",
                    ["Meta Ads (Facebook/Instagram)", "Google Ads", "TikTok", "LinkedIn", 
                     "YouTube", "Mídia Programática", "Twitter", "Pinterest"],
                    default=["Meta Ads (Facebook/Instagram)", "Google Ads"]
                )
                
                localizacao_primaria = st.text_input(
                    "Localização Primária (Estados)*",
                    placeholder="Ex: MT, GO, RS",
                    value="MT, GO, RS"
                )
                
                localizacao_secundaria = st.text_input(
                    "Localização Secundária (Cidades)",
                    placeholder="Ex: Rio de Janeiro, São Paulo, Cuiabá",
                    value="Rio de Janeiro, São Paulo, Cuiabá"
                )
                
                tipo_publico = st.selectbox(
                    "Tipo de Público*",
                    ["Interesses", "Lookalike Audience (LAL)", "Base de Clientes", 
                     "Retargeting", "Comportamento", "Demográfico"],
                    index=0
                )
                
                tipo_criativo = st.multiselect(
                    "Tipos de Criativo*",
                    ["Estático", "Vídeo", "Carrossel", "Motion", "Story", "Coleção"],
                    default=["Estático", "Vídeo"]
                )
            
            st.markdown("**Selecione e defina metas para os OKRs relevantes:**")
            
            # Criar checkboxes e inputs para métricas da etapa selecionada
            metricas = {}
            for metrica in METRICAS_POR_ETAPA_PLANEJAMENTO[etapa_funil]:
                col1, col2 = st.columns([1, 3])
                with col1:
                    selecionada = st.checkbox(metrica, value=True, key=f"check_{metrica}")
                with col2:
                    valor = st.text_input(
                        f"Meta para {metrica}",
                        placeholder=f"Ex: 500.000 {metrica.split()[0]}" if " " in metrica else f"Ex: 500.000 {metrica}",
                        key=f"input_{metrica}",
                        disabled=not selecionada
                    )
                metricas[metrica] = {
                    'selecionada': selecionada,
                    'valor': valor,
                    'descricao': DESCRICOES_METRICAS.get(metrica, "")
                }
            
            detalhes_acao = st.text_area(
                "Detalhes da Ação*",
                placeholder="Descreva o produto/serviço/evento que será promovido",
                value="Campanha de produtos agrícolas para pequenos e médios produtores"
            )
            
            observacoes = st.text_area(
                "Observações Adicionais",
                placeholder="Informações extras sobre a campanha, concorrentes, etc."
            )
            
            submitted = st.form_submit_button("Gerar Plano de Mídia")
        
        if submitted:
            if not objetivo_campanha or not tipo_campanha or not budget or not ferramentas or not localizacao_primaria or not detalhes_acao:
                st.error("Por favor, preencha todos os campos obrigatórios (*)")
            else:
                # Armazenar parâmetros na sessão
                params = {
                    'objetivo_campanha': objetivo_campanha,
                    'tipo_campanha': tipo_campanha,
                    'etapa_funil': etapa_funil,
                    'budget': budget,
                    'periodo': periodo,
                    'ferramentas': ferramentas,
                    'localizacao_primaria': localizacao_primaria,
                    'localizacao_secundaria': localizacao_secundaria,
                    'tipo_publico': tipo_publico,
                    'tipo_criativo': tipo_criativo,
                    'metricas': metricas,
                    'detalhes_acao': detalhes_acao,
                    'observacoes': observacoes
                }
                
                st.session_state.current_step_planejamento = 1
                st.session_state.params_planejamento = params
                
                # Gerar todo o conteúdo de uma vez
                with st.spinner(f'Gerando plano completo para {etapa_funil} do funil...'):
                    st.session_state.plano_completo['recomendacao_estrategica'] = gerar_recomendacao_estrategica(params)
                    st.session_state.plano_completo['distribuicao_budget'] = gerar_distribuicao_budget(params, st.session_state.plano_completo['recomendacao_estrategica'])
                    st.session_state.plano_completo['previsao_resultados'] = gerar_previsao_resultados(params, st.session_state.plano_completo['recomendacao_estrategica'], st.session_state.plano_completo['distribuicao_budget'])
                    st.session_state.plano_completo['recomendacoes_publico'] = gerar_recomendacoes_publico(params, st.session_state.plano_completo['recomendacao_estrategica'])
                    st.session_state.plano_completo['cronograma'] = gerar_cronograma(params, st.session_state.plano_completo['recomendacao_estrategica'], st.session_state.plano_completo['distribuicao_budget'])
        
        # Exibir resultados
        if st.session_state.current_step_planejamento >= 1 and 'params_planejamento' in st.session_state:
            etapa_funil = st.session_state.params_planejamento.get('etapa_funil', 'Topo')
            st.success(f"**Etapa do Funil Selecionada:** {etapa_funil}")
            
            # Verificar se 'metricas' existe nos parâmetros
            if 'metricas' in st.session_state.params_planejamento:
                okrs_selecionados = [k for k, v in st.session_state.params_planejamento['metricas'].items() if v['selecionada']]
                metas_definidas = [f"{k}: {v['valor']}" for k, v in st.session_state.params_planejamento['metricas'].items() if v['selecionada'] and v['valor']]
                
                if okrs_selecionados:
                    st.info(f"**OKRs Selecionados:** {', '.join(okrs_selecionados)}")
                if metas_definidas:
                    st.info(f"**Metas Definidas:** {', '.join(metas_definidas)}")
            else:
                st.warning("Nenhuma métrica foi configurada ainda.")
            
            st.markdown("## 📌 Recomendação Estratégica")
            st.markdown(st.session_state.plano_completo.get('recomendacao_estrategica', 'Em processamento...'))
            
            st.markdown("## 📊 Distribuição de Budget")
            st.markdown(st.session_state.plano_completo.get('distribuicao_budget', 'Em processamento...'))
            
            st.markdown("## 📈 Previsão de Resultados")
            st.markdown(st.session_state.plano_completo.get('previsao_resultados', 'Em processamento...'))
            
            st.markdown("## 🎯 Recomendações de Público")
            st.markdown(st.session_state.plano_completo.get('recomendacoes_publico', 'Em processamento...'))
            
            st.markdown("## 📅 Cronograma Sugerido")
            st.markdown(st.session_state.plano_completo.get('cronograma', 'Em processamento...'))
            
            # Botão para baixar o plano completo
            if all(key in st.session_state.plano_completo for key in ['recomendacao_estrategica', 'distribuicao_budget', 'previsao_resultados', 'recomendacoes_publico', 'cronograma']):
                plano_completo = "\n\n".join([
                    f"# 📊 Plano de Mídia Completo ({etapa_funil} do Funil)\n",
                    f"**Campanha:** {st.session_state.params_planejamento['objetivo_campanha']}",
                    f"**Budget:** R$ {st.session_state.params_planejamento['budget']:,.2f}",
                    f"**Período:** {st.session_state.params_planejamento['periodo']}",
                    f"**OKRs Selecionados:** {', '.join(okrs_selecionados) if okrs_selecionados else 'A serem otimizados'}",
                    f"**Metas Definidas:** {', '.join(metas_definidas) if metas_definidas else 'Nenhuma específica'}\n",
                    "## 📌 Recomendação Estratégica",
                    st.session_state.plano_completo['recomendacao_estrategica'],
                    "## 📊 Distribuição de Budget",
                    st.session_state.plano_completo['distribuicao_budget'],
                    "## 📈 Previsão de Resultados",
                    st.session_state.plano_completo['previsao_resultados'],
                    "## 🎯 Recomendações de Público",
                    st.session_state.plano_completo['recomendacoes_publico'],
                    "## 📅 Cronograma Sugerido",
                    st.session_state.plano_completo['cronograma']
                ])
                
                st.download_button(
                    label="📥 Baixar Plano Completo",
                    data=plano_completo,
                    file_name=f"plano_midia_{etapa_funil}_{st.session_state.params_planejamento['objetivo_campanha'][:30]}.md",
                    mime="text/markdown"
                )

    with tab2:
        st.header("Exemplos por Etapa do Funil")
        
        tab_topo, tab_meio, tab_fundo = st.tabs(["Topo", "Meio", "Fundo"])
        
        with tab_topo:
            st.markdown("""
            ### 📋 Exemplo - Topo do Funil (Awareness)
            **Campanha:** Conscientização da Marca X  
            **Objetivo:** Aumentar reconhecimento de marca  
            **Etapa do Funil:** Topo  
            **OKRs Típicos:** Impressões, Alcance, Frequência, CPM  
            """)
            
            st.markdown("""
            #### 🎯 Metas Recomendadas:
            - Impressões: 5.000.000
            - Alcance: 2.200.000
            - Frequência média: 2.3
            - CPM: R$ 15-20
            
            #### 📊 Alocação Recomendada:
            | Plataforma | % Budget | Valor (R$) | Criativos Principais |
            |------------|----------|------------|----------------------|
            | Meta Ads | 50% | 75.000 | Vídeo (60%), Estático (40%) |
            | YouTube | 30% | 45.000 | Vídeo (100%) |
            | Programática | 20% | 30.000 | Banner (70%), Vídeo (30%) |
            """)
        
        with tab_meio:
            st.markdown("""
            ### 📋 Exemplo - Meio do Funil (Consideração)
            **Campanha:** Engajamento Produto Y  
            **Objetivo:** Gerar interesse no produto  
            **Etapa do Funil:** Meio  
            **OKRs Típicos:** CTR, Video Views, Engajamento  
            """)
            
            st.markdown("""
            #### 🎯 Metas Recomendadas:
            - CTR: 1.8-2.5%
            - Video Views: 500.000
            - Engajamento: 3.5%
            
            #### 📊 Alocação Recomendada:
            | Plataforma | % Budget | Valor (R$) | Criativos Principais |
            |------------|----------|------------|----------------------|
            | Meta Ads | 40% | 32.000 | Carrossel (50%), Vídeo (50%) |
            | LinkedIn | 30% | 24.000 | Estático (70%), Vídeo (30%) |
            | Google Ads | 30% | 24.000 | Display (60%), Vídeo (40%) |
            """)
        
        with tab_fundo:
            st.markdown("""
            ### 📋 Exemplo - Fundo do Funil (Conversão)
            **Campanha:** Vendas Produto Z  
            **Objetivo:** Gerar vendas diretas  
            **Etapa do Funil:** Fundo  
            **OKRs Típicos:** Conversões, ROAS, CPA  
            """)
            
            st.markdown("""
            #### 🎯 Metas Recomendadas:
            - Conversões: 1.500
            - ROAS: 3.5x
            - CPA: R$ 80-100
            
            #### 📊 Alocação Recomendada:
            | Plataforma | % Budget | Valor (R$) | Criativos Principais |
            |------------|----------|------------|----------------------|
            | Meta Ads | 60% | 72.000 | Coleção (70%), Estático (30%) |
            | Google Ads | 40% | 48.000 | Shopping (100%) |
            """)

# =============================================================================
# FUNÇÕES PARA GERAÇÃO DE RELATÓRIO AVANÇADO
# =============================================================================

def gerar_relatorio_llm(df, metricas, colunas_selecionadas, tipo_relatorio, cliente_info=None, df_anterior=None, usuario_id=None, plataformas=None):
    """Gera um relatório analítico usando LLM e salva no MongoDB"""
    if not gemini_api_key:
        relatorio_completo = {
            "partes": [{"titulo": "Aviso", "conteudo": "🔒 Relatório avançado desabilitado. Configure a API key do Gemini para ativar esta funcionalidade."}],
            "texto_completo": "# Relatório de Campanhas\n\n🔒 Relatório avançado desabilitado. Configure a API key do Gemini para ativar esta funcionalidade."
        }
        return relatorio_completo
    
    try:
        if not isinstance(df, pd.DataFrame) or df.empty:
            relatorio_completo = {
                "partes": [{"titulo": "Erro", "conteudo": "Dados inválidos para gerar relatório"}],
                "texto_completo": "# Relatório de Campanhas\n\n## Erro\n\nDados inválidos para gerar relatório"
            }
            return relatorio_completo

        # Configuração inicial do cliente Gemini
        client = genai.Client(api_key=gemini_api_key)
        model_id = "gemini-2.0-flash"
        
        dados_para_llm = ""
        
        # Adicionar informações sobre as plataformas
        if plataformas:
            dados_para_llm += f"## Plataformas Analisadas: {', '.join(plataformas)}\n\n"
        
        dados_para_llm += "## Resumo Estatístico - Mês Atual:\n"
        for col in colunas_selecionadas:
            if col in metricas:
                stats = metricas[col]
                dados_para_llm += f"- {col}: Média={stats['média']:.2f}, Mediana={stats['mediana']:.2f}, Min={stats['min']:.2f}, Max={stats['max']:.2f}\n"
        
        if df_anterior is not None and isinstance(df_anterior, pd.DataFrame) and not df_anterior.empty:
            metricas_anterior = calcular_metricas(df_anterior)
            dados_para_llm += "\n## Análise Comparativa Mensal:\n"
            
            for col in colunas_selecionadas:
                if col in metricas and col in metricas_anterior:
                    media_atual = metricas[col]['média']
                    media_anterior = metricas_anterior[col]['média']
                    variacao = ((media_atual - media_anterior) / media_anterior) * 100 if media_anterior != 0 else 0
                    
                    dados_para_llm += (f"- {col}: {media_atual:.2f} (Mês Atual) vs {media_anterior:.2f} (Mês Anterior) → "
                                    f"{'↑' if variacao > 0 else '↓'} {abs(variacao):.1f}%\n")
        
        dados_para_llm += "\n## Melhores Campanhas - Mês Atual:\n"
        for col in colunas_selecionadas[:10]:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                top3 = df.nlargest(3, col)[['Campanha', 'Plataforma', col]]
                dados_para_llm += f"- {col}:\n"
                for _, row in top3.iterrows():
                    dados_para_llm += f"  - {row['Campanha']} ({row['Plataforma']}): {row[col]:.2f}\n"
        
        if df_anterior is not None and isinstance(df_anterior, pd.DataFrame) and not df_anterior.empty:
            dados_para_llm += "\n## Insights de Correlação:\n"
            dados_para_llm += "  - Exemplo de análise combinada que será gerada pelo LLM:\n"
            dados_para_llm += "    * Se CTR aumentou mas Conversões caíram, pode indicar tráfego menos qualificado\n"
            dados_para_llm += "    * Se Custo por Conversão caiu e Conversões aumentaram, indica eficiência melhorada\n"
            dados_para_llm += "    * Se Impressões caíram mas Engajamentos aumentaram, pode indicar público mais segmentado\n"
        
        with st.spinner("🧠 Gerando relatório avançado com IA..."):
            relatorio_completo = {
                "partes": [],
                "texto_completo": "# Relatório de Campanhas\n\n"
            }
            
            texto_completo_md = "# Relatório de Campanhas\n\n"
            
            prompts = []
            if tipo_relatorio == "técnico":
                prompts = [
                    ("1. Introdução com visão geral", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    - Considere que os dados vêm de múltiplas plataformas: {plataformas if plataformas else 'Não especificadas'}

                    Dê apenas um panorama geral sobre os dados com os pontos:

                    - Visão geral do desempenho das campanhas em todas as plataformas
                    - Contexto sobre os dados analisados
                    - Destaque inicial dos pontos mais relevantes
                    - Comparação entre o desempenho nas diferentes plataformas
                    
                    Dados: {dados_para_llm}
                    
                    """),
                    ("2. Análise de cada métrica selecionada", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    - Considere que os dados vêm de múltiplas plataformas: {plataformas if plataformas else 'Não especificadas'}

                    Faça apenas uma análise técnica detalhada de cada métrica selecionada, com os pontos:
                    - Significado de cada métrica
                    - Performance em relação aos benchmarks do setor
                    - Relação com o tipo de campanha
                    - Comparação entre plataformas quando aplicável
                    
                    Dados: {dados_para_llm}
 
                    """),
                    ("3. Comparativo mensal detalhado", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    - Considere que os dados vêm de múltiplas plataformas: {plataformas if plataformas else 'Não especificadas'}
                    - Considere os objetivos das campanhas (que podem ser deduzidos pelos seus nomes) quando fizer sua análise
                    Faça apenas um comparativo mensal detalhado com os pontos:
                    Analise comparativamente os dados com o mês anterior (quando disponível):
                    - Variações percentuais significativas
                    - Tendências identificadas
                    - Comparação entre plataformas
                    
                    Dados: {dados_para_llm}

                    """),
                    ("4. Insights sobre correlações", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    - Considere que os dados vêm de múltiplas plataformas: {plataformas if plataformas else 'Não especificadas'}
                    - Considere os objetivos das campanhas (que podem ser deduzidos pelos seus nomes) quando fizer sua análise
                
                    Apenas Identifique correlações importantes entre as métricas com os pontos:
                    - Relações causa-efeito
                    - Padrões de desempenho
                    - Anomalias e outliers
                    - Comparações entre plataformas
                    - EX: Se métrica X subiu e métrica Y abaixou, isso significa que...
                    - EX: Como as diferentes plataformas se complementam no funnel
                    
                    Dados: {dados_para_llm}
        
                    """),
                    ("5. Recomendações técnicas", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    - Considere que os dados vêm de múltiplas plataformas: {plataformas if plataformas else 'Não especificadas'}
                    - Considere os objetivos das campanhas (que podem ser deduzidos pelos seus nomes) quando fizer sua análise
                    Apenas gere recomendações técnicas específicas baseadas na análise com os pontos:
                    - Ajustes em campanhas por plataforma
                    - Otimizações sugeridas para cada plataforma
                    - Alertas sobre problemas identificados
                    - Sugestões de realocação de orçamento entre plataformas
                    
                    Dados: {dados_para_llm}
 
                    """),
                    ("6. Conclusão com resumo executivo", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    - Considere que os dados vêm de múltiplas plataformas: {plataformas if plataformas else 'Não especificadas'}
                    - Considere os objetivos das campanhas (que podem ser deduzidos pelos seus nomes) quando fizer sua análise
                    Apenas Conclua com um resumo executivo técnico com os pontos:
                    - Principais achados por plataforma
                    - Recomendações prioritárias
                    - Próximos passos sugeridos
                    - Visão integrada do desempenho multicanal
                    
                    Dados: {dados_para_llm}

                    """)
                ]
            else:
                prompts = [
                    ("1. Visão geral simplificada", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    - Considere que os dados vêm de múltiplas plataformas: {plataformas if plataformas else 'Não especificadas'}
                    - Considere os objetivos das campanhas (que podem ser deduzidos pelos seus nomes) quando fizer sua análise
                    Você é um estrategista de marketing. Apenas Gere uma visão geral simplificada em português com os pontos:
                    - Principais resultados por plataforma
                    - Destaques e preocupações
                    - Contexto estratégico multicanal
                    
                    Dados: {dados_para_llm}
        
                    """),
                    ("2. Principais destaques e preocupações", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    - Considere que os dados vêm de múltiplas plataformas: {plataformas if plataformas else 'Não especificadas'}
                    - Considere os objetivos das campanhas (que podem ser deduzidos pelos seus nomes) quando fizer sua análise
                    Destaque os pontos mais relevantes e preocupações:

                    Apenas apresente os principais destaques e preocupações com os pontos:
                    - Comparações mensais por plataforma
                    - Variações significativas
                    - Impacto estratégico dado o tipo de campanha
                    - Alinhamento com objetivos dado o tipo de campanha
                    - Comparação entre desempenho nas diferentes plataformas
                    
                    Dados: {dados_para_llm}

                    """),
                    ("3. Análise estratégica do desempenho", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    - Considere que os dados vêm de múltiplas plataformas: {plataformas if plataformas else 'Não especificadas'}
                    - Considere os objetivos das campanhas (que podem ser deduzidos pelos seus nomes) quando fizer sua análise
                    Apenas Analise o desempenho com focus em tendências com os pontos:
                    - Padrões de longo prazo
                    - Eficácia estratégica por plataforma
                    - Alinhamento com objetivos dado o tipo de campanha
                    - Sinergias entre plataformas
                    
                    Dados: {dados_para_llm}

                    """),
                    ("4. Relações entre métricas", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    - Considere que os dados vêm de múltiplas plataformas: {plataformas if plataformas else 'Não especificadas'}
                    - Considere os objetivos das campanhas (que podem ser deduzidos pelos seus nomes) quando fizer sua análise

                    Apenas Explique como as métricas se relacionam e impactam os resultados com os pontos:
                    - Conexões importantes entre plataformas
                    - Trade-offs identificados
                    - Sinergias encontradas entre canais
                    - Relações causa-efeito
                    - Tire insights sobre os trade offs entre as variações das métricas. Relacione-as e tire conclusões sobre o que está acontecendo.
                    - Analise como as diferentes plataformas contribuem para o funnel completo
                    
                    Dados: {dados_para_llm}

                    """),
                    ("5. Recomendações de alto nível", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    - Considere que os dados vêm de múltiplas plataformas: {plataformas if plataformas else 'Não especificadas'}
                    - Considere os objetivos das campanhas (que podem ser deduzidos pelos seus nomes) quando fizer sua análise
                    Apenas Gere recomendações estratégicas com os pontos:
                    - Direcionamentos gerais por plataforma
                    - Priorizações sugeridas
                    - Ajustes recomendados no mix de canais
                    - Sugestões de realocação de orçamento entre plataformas
                    
                    Dados: {dados_para_llm}

                    """),
                    ("6. Próximos passos sugeridos", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    - Considere que os dados vêm de múltiplas plataformas: {plataformas if plataformas else 'Não especificadas'}
                    - Considere os objetivos das campanhas (que podem ser deduzidos pelos seus nomes) quando fizer sua análise
                    Apenas Defina os próximos passos estratégicos com os pontos:
                    - Ações imediatas por plataforma
                    - Monitoramentos necessários
                    - Planejamento futuro multicanal
                    - Experimentos sugeridos para otimizar o mix de canals
                    
                    Dados: {dados_para_llm}

                    """)
                ]
            
            for titulo, prompt in prompts:
                with st.spinner(f"Gerando {titulo.lower()}..."):
                    response = client.models.generate_content(
                        model='gemini-2.0-flash',
                        contents=prompt
                    )
                    parte_conteudo = response.text
                    
                    texto_completo_md += f"## {titulo}\n\n{parte_conteudo}\n\n"
                    
                    parte_relatorio = {
                        "titulo": titulo,
                        "conteudo": parte_conteudo
                    }
                    relatorio_completo["partes"].append(parte_relatorio)
            
            # Adicionando pesquisa de novidades em otimização de campanhas
            with st.spinner("🔍 Buscando novidades em otimização de campanhas..."):
                try:
                    google_search_tool = Tool(
                        google_search=GoogleSearch()
                    )
                    
                    pesquisa = client.models.generate_content(
                        model=model_id,
                        contents="Faça uma pesquisa sobre notícias sobre novidades em otimização de campanhas digitais multicanal. Inclua apenas informações relevantes e atualizadas.",
                        config=GenerateContentConfig(
                            tools=[google_search_tool],
                            response_modalities=["TEXT"],
                        )
                    )
                    
                    if pesquisa.text:
                        parte_pesquisa = {
                            "titulo": "🔍 Novidades em Otimização de Campanhas (Pesquisa Web)",
                            "conteudo": pesquisa.text
                        }
                        relatorio_completo["partes"].append(parte_pesquisa)
                        texto_completo_md += f"## 🔍 Novidades em Otimização de Campanhas (Pesquisa Web)\n\n{pesquisa.text}\n\n"
                except Exception as e:
                    st.error(f"Erro na pesquisa web: {str(e)}")
                    parte_pesquisa = {
                        "titulo": "🔍 Novidades em Otimização de Campanhas",
                        "conteudo": "Não foi possível realizar a pesquisa web no momento."
                    }
                    relatorio_completo["partes"].append(parte_pesquisa)
            
            relatorio_completo["texto_completo"] = texto_completo_md
            
            # Gerar nome do relatório com informações do cliente e plataformas
            nome_relatorio = gerar_nome_relatorio(cliente_info, plataformas, tipo_relatorio)
            
            relatorio_data = {
                "titulo": nome_relatorio,  # Adicionando título descritivo
                "tipo": tipo_relatorio,
                "partes": relatorio_completo["partes"],
                "texto_completo": relatorio_completo["texto_completo"],
                "metricas_analisadas": colunas_selecionadas,
                "data_geracao": datetime.now(),
                "cliente": cliente_info if cliente_info else {"nome": "Não especificado", "id": "", "tags": []},
                "status": "ativo",
                "comparativo_mensal": df_anterior is not None,
                "plataformas": plataformas if plataformas else []
            }
            
            relatorio_id = salvar_relatorio_mongodb(relatorio_data, usuario_id)
            if relatorio_id:
                st.success("✅ Relatório salvo no banco de dados com sucesso!")
            
            return relatorio_completo
        
    except Exception as e:
        error_msg = f"Erro ao gerar relatório: {str(e)}"
        return {
            "partes": [{"titulo": "Erro", "conteudo": error_msg}],
            "texto_completo": f"# Relatório de Campanhas\n\n## Erro\n\n{error_msg}"
        }

# =============================================================================
# FUNÇÕES PARA COMBINAR RELATÓRIOS COM IA
# =============================================================================

def combinar_relatorios_com_llm(relatorio1_id, relatorio2_id, usuario_id):
    """Combina dois relatórios em um único relatório unificado usando LLM"""
    try:
        relatorio1 = obter_relatorio_completo(relatorio1_id)
        relatorio2 = obter_relatorio_completo(relatorio2_id)
        
        if not relatorio1 or not relatorio2:
            return None, "Um ou ambos os relatórios não foram encontrados"
        
        if not gemini_api_key:
            return None, "API key do Gemini não configurada. Não é possível combinar relatórios com IA."
        
        # Configuração do cliente Gemini
        client = genai.Client(api_key=gemini_api_key)
        
        # Extrair textos completos dos relatórios
        texto_relatorio1 = relatorio1.get("texto_completo", "")
        texto_relatorio2 = relatorio2.get("texto_completo", "")
        
        # Informações sobre os relatórios
        info_relatorio1 = f"""
        Cliente: {relatorio1.get('cliente', {}).get('nome', 'Não especificado')}
        Tipo: {relatorio1.get('tipo', 'Não especificado')}
        Data: {relatorio1['data_geracao'].strftime('%d/%m/%Y')}
        Plataformas: {', '.join(relatorio1.get('plataformas', []))}
        """
        
        info_relatorio2 = f"""
        Cliente: {relatorio2.get('cliente', {}).get('nome', 'Não especificado')}
        Tipo: {relatorio2.get('tipo', 'Não especificado')}
        Data: {relatorio2['data_geracao'].strftime('%d/%m/%Y')}
        Plataformas: {', '.join(relatorio2.get('plataformas', []))}
        """
        
        with st.spinner("🧠 Combinando relatórios com IA..."):
            # Criar relatório combinado
            relatorio_combinado = {
                "tipo": "combinado-ia",
                "partes": [],
                "texto_completo": "# Relatório Combinado com IA\n\n",
                "data_geracao": datetime.now(),
                "status": "ativo",
                "usuario_id": usuario_id,
                "relatorios_originais": [relatorio1_id, relatorio2_id],
                "cliente": {
                    "nome": f"Combinação IA: {relatorio1.get('cliente', {}).get('nome', 'Relatório 1')} + {relatorio2.get('cliente', {}).get('nome', 'Relatório 2')}",
                    "id": "combinado-ia"
                },
                "plataformas": list(set(relatorio1.get('plataformas', []) + relatorio2.get('plataformas', [])))
            }
            
            texto_completo_md = "# 📊 Relatório Combinado com Inteligência Artificial\n\n"
            
            # Introdução combinada gerada por IA
            prompt_intro = f"""
            Você é um analista de marketing senior. Crie uma introdução para um relatório combinado que integra insights de dois relatórios diferentes.

            RELATÓRIO 1:
            {info_relatorio1}

            RELATÓRIO 2:
            {info_relatorio2}

            Gere uma introdução profissional que:
            1. Apresente os dois relatórios que estão sendo combinados
            2. Explique o valor estratégico de combinar estas análises
            3. Destaque o que os leitores podem esperar deste relatório integrado
            4. Mantenha um tom profissional и analítico

            Retorne apenas o texto da introdução, sem marcações adicionais.
            """
            
            response_intro = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt_intro
            )
            intro_conteudo = response_intro.text
            
            parte_intro = {
                "titulo": "📋 Introdução - Análise Combinada",
                "conteudo": intro_conteudo
            }
            relatorio_combinado["partes"].append(parte_intro)
            texto_completo_md += f"## {parte_intro['titulo']}\n\n{parte_intro['conteudo']}\n\n"
            
            # Identificar seções comuns
            secoes_relatorio1 = [p["titulo"] for p in relatorio1.get("partes", [])]
            secoes_relatorio2 = [p["titulo"] for p in relatorio2.get("partes", [])]
            secoes_comuns = set(secoes_relatorio1) & set(secoes_relatorio2)
            
            # Processar cada seção comum com IA
            for secao in sorted(secoes_comuns):
                # Encontrar conteúdos desta seção em ambos os relatórios
                conteudo_relatorio1 = next((p["conteudo"] for p in relatorio1.get("partes", []) if p["titulo"] == secao), "")
                conteudo_relatorio2 = next((p["conteudo"] for p in relatorio2.get("partes", []) if p["titulo"] == secao), "")
                
                prompt_combinacao = f"""
                Você é um analista de marketing especializado em análise integrada de dados. 
                Combine as análises da mesma seção de dois relatórios diferentes para criar uma visão unificada.

                SEÇÃO: {secao}

                ANÁLISE DO RELATÓRIO 1:
                {conteudo_relatorio1}

                ANÁLISE DO RELATÓRIO 2:
                {conteudo_relatorio2}

                CONTEXTO DOS RELATÓRIOS:
                Relatório 1: {info_relatorio1}
                Relatório 2: {info_relatorio2}

                Gere uma análise combinada que:
                1. Identifique pontos em comum entre as duas análises
                2. Destaque diferenças significativas e suas possíveis causas
                3. Crie insights novos que só são possíveis ao combinar os dois relatórios
                4. Forneça recomendações integradas baseadas na combinação
                5. Mantenha a estrutura analítica profissional

                Retorne apenas o texto da análise combinada, sem marcações adicionais.
                """
                
                response_combinacao = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=prompt_combinacao
                )
                conteudo_combinado = response_combinacao.text
                
                parte_combinada = {
                    "titulo": f"🔗 {secao} (Análise Integrada)",
                    "conteudo": conteudo_combinado
                }
                
                relatorio_combinado["partes"].append(parte_combinada)
                texto_completo_md += f"## {parte_combinada['titulo']}\n\n{parte_combinada['conteudo']}\n\n"
            
            # Análise de seções únicas
            secoes_unicas_relatorio1 = set(secoes_relatorio1) - secoes_comuns
            secoes_unicas_relatorio2 = set(secoes_relatorio2) - secoes_comuns
            
            if secoes_unicas_relatorio1:
                texto_completo_md += "## 📌 Seções Exclusivas do Relatório 1\n\n"
                for secao in sorted(secoes_unicas_relatorio1):
                    conteudo = next((p["conteudo"] for p in relatorio1.get("partes", []) if p["titulo"] == secao), "")
                    parte_unica = {
                        "titulo": f"📌 {secao} (Exclusivo Relatório 1)",
                        "conteudo": f"**Fonte: {relatorio1.get('cliente', {}).get('nome', 'Relatório 1')}**\n\n{conteudo}"
                    }
                    relatorio_combinado["partes"].append(parte_unica)
                    texto_completo_md += f"### {parte_unica['titulo']}\n\n{parte_unica['conteudo']}\n\n"
            
            if secoes_unicas_relatorio2:
                texto_completo_md += "## 📌 Seções Exclusivas do Relatório 2\n\n"
                for secao in sorted(secoes_unicas_relatorio2):
                    conteudo = next((p["conteudo"] for p in relatorio2.get("partes", []) if p["titulo"] == secao), "")
                    parte_unica = {
                        "titulo": f"📌 {secao} (Exclusivo Relatório 2)",
                        "conteudo": f"**Fonte: {relatorio2.get('cliente', {}).get('nome', 'Relatório 2')}**\n\n{conteudo}"
                    }
                    relatorio_combinado["partes"].append(parte_unica)
                    texto_completo_md += f"### {parte_unica['titulo']}\n\n{parte_unica['conteudo']}\n\n"
            
            # Conclusão integrada gerada por IA
            prompt_conclusao = f"""
            Você é um estrategista de marketing. Crie uma conclusão poderosa para o relatório combinado.

            CONTEXTO:
            Relatório 1: {info_relatorio1}
            Relatório 2: {info_relatorio2}

            Com base na análise combinada dos dois relatórios, gere uma conclusão que:
            1. Sintetize os insights mais importantes da análise integrada
            2. Destaque oportunidades estratégicas identificadas
            3. Forneça recomendações acionáveis baseadas na combinação dos dados
            4. Indique próximos passos e métricas para monitorar
            5. Explique o valor único que esta análise combinada proporciona

            Retorne apenas o texto da conclusão, sem marcações adicionais.
            """
            
            response_conclusao = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt_conclusao
            )
            conclusao_conteudo = response_conclusao.text
            
            parte_conclusao = {
                "titulo": "🎯 Conclusão e Recomendações Integradas",
                "conteudo": conclusao_conteudo
            }
            relatorio_combinado["partes"].append(parte_conclusao)
            texto_completo_md += f"## {parte_conclusao['titulo']}\n\n{parte_conclusao['conteudo']}\n\n"
            
            relatorio_combinado["texto_completo"] = texto_completo_md
            
            # Gerar nome descritivo para o relatório combinado
            nome_combinado = f"relatorio_combinado_ia_{relatorio1.get('cliente', {}).get('nome', 'Relat1').replace(' ', '_')}_{relatorio2.get('cliente', {}).get('nome', 'Relat2').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}"
            relatorio_combinado["titulo"] = nome_combinado
            
            # Salvar no banco de dados
            relatorio_id = salvar_relatorio_mongodb(relatorio_combinado, usuario_id)
            return relatorio_id, "Relatório combinado com IA criado com sucesso"
        
    except Exception as e:
        return None, f"Erro ao combinar relatórios com IA: {str(e)}"

# =============================================================================
# FUNÇÕES PARA INTERFACE PRINCIPAL
# =============================================================================

def mostrar_tela_login():
    """Mostra a tela de login/cadastro"""
    st.title("🔐 Login / Cadastro")
    
    tab_login, tab_cadastro = st.tabs(["Login", "Cadastro"])
    
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            senha = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar")
            
            if submit:
                sucesso, usuario, mensagem = verificar_login(email, senha)
                if sucesso:
                    st.session_state["usuario"] = usuario
                    st.session_state["autenticado"] = True
                    st.success("Login bem-sucedido! Redirecionando...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(mensagem)
                    
    with tab_cadastro:
        with st.form("cadastro_form"):
            nome = st.text_input("Nome Completo")
            email_cadastro = st.text_input("Email")
            senha_cadastro = st.text_input("Senha", type="password")
            confirmar_senha = st.text_input("Confirmar Senha", type="password")
            submit_cadastro = st.form_submit_button("Criar Conta")
            
            if submit_cadastro:
                if senha_cadastro != confirmar_senha:
                    st.error("As senhas não coincidem")
                elif len(senha_cadastro) < 6:
                    st.error("A senha deve ter pelo menos 6 caracteres")
                else:
                    sucesso, mensagem = criar_usuario(email_cadastro, senha_cadastro, nome)
                    if sucesso:
                        st.success(mensagem + " Agora faça login.")
                    else:
                        st.error(mensagem)

def mostrar_app_principal():
    """Mostra o aplicativo principal após o login"""
    usuario = st.session_state.get("usuario", {})
    
    with st.sidebar:
        st.markdown(f"### 👤 {usuario.get('nome', 'Usuário')}")
        st.markdown(f"✉️ {usuario.get('email', '')}")
        
        if st.button("🚪 Sair"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.title("Agente Performance")
    
    # Criar abas principais incluindo as novas funcionalidades
    tab_analise, tab_campanha_a_campanha, tab_relatorio_pdf, tab_relatorios, tab_planejamento = st.tabs([
        "📈 Análise de Campanhas", 
        "🔍 Análise Campanha a Campanha", 
        "📊 Gerar Relatório PDF", 
        "🗂 Meus Relatórios", 
        "🎯 Planejamento de Mídia"
    ])
    
    with tab_analise:
        if 'dados_atual' not in st.session_state:
            st.session_state.dados_atual = None
            st.session_state.dados_anterior = None
            st.session_state.plataformas_selecionadas = []
        
        st.subheader("Upload de Arquivos CSV")
        
        # Usar o upload unificado
        dados_atual, dados_anterior = criar_interface_upload_unificado()
        
        # Atualizar dados na sessão
        if dados_atual:
            st.session_state.dados_atual = dados_atual
        if dados_anterior:
            st.session_state.dados_anterior = dados_anterior
        
        with st.expander("ℹ️ Informações do Cliente (Opcional)"):
            cliente_nome = st.text_input("Nome do Cliente")
            cliente_id = st.text_input("ID do Cliente (se aplicável)")
            cliente_tags = st.text_input("Tags (separadas por vírgula)")
            
            cliente_info = {
                "nome": cliente_nome,
                "id": cliente_id,
                "tags": [tag.strip() for tag in cliente_tags.split(",")] if cliente_tags else []
            }
        
        if st.session_state.dados_atual:
            # Aqui você pode adicionar a análise existente que já estava no código original
            pass
    
    with tab_campanha_a_campanha:
        st.markdown("## 🔍 Análise Detalhada Campanha a Campanha")
        
        if st.session_state.dados_atual:
            resultados = analise_campanha_a_campanha(
                st.session_state.dados_atual,
                st.session_state.dados_anterior
            )
            
            if resultados:
                # Opção para exportar análise
                if st.button("📥 Exportar Análise Detalhada"):
                    # Criar um DataFrame com os resultados
                    dados_exportacao = []
                    
                    for plataforma, info in resultados.items():
                        if info['dados_atual'] is not None and not info['dados_atual'].empty:
                            dados_exportacao.append({
                                'Plataforma': plataforma,
                                'Campanha': info['campanha'],
                                'Status': 'Analisada'
                            })
                    
                    if dados_exportacao:
                        df_export = pd.DataFrame(dados_exportacao)
                        
                        csv = df_export.to_csv(index=False)
                        st.download_button(
                            label="📥 Baixar CSV",
                            data=csv,
                            file_name=f"analise_campanhas_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
        else:
            st.info("ℹ️ Carregue os dados do mês atual na aba 'Análise de Campanhas' para usar esta funcionalidade")
    
    with tab_relatorio_pdf:
        st.markdown("## 📊 Gerar Relatório Mensal em PDF")
        
        if st.session_state.dados_atual:
            st.info("Clique no botão abaixo para gerar um relatório comparativo mensal em PDF")
            
            # Informações do relatório
            col1, col2 = st.columns(2)
            with col1:
                titulo_relatorio = st.text_input(
                    "Título do Relatório",
                    value="Relatório Mensal de Performance"
                )
            
            with col2:
                mes_referencia = st.selectbox(
                    "Mês de Referência",
                    options=[
                        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
                    ],
                    index=datetime.now().month - 1
                )
            
            if st.button("📄 Gerar Relatório PDF"):
                with st.spinner("Gerando relatório PDF..."):
                    # Informações do cliente
                    cliente_info = {
                        "nome": st.session_state.get("cliente_nome", "Cliente"),
                        "id": st.session_state.get("cliente_id", "")
                    }
                    
                    pdf_buffer = gerar_relatorio_pdf(
                        st.session_state.dados_atual,
                        st.session_state.dados_anterior,
                        cliente_info
                    )
                    
                    st.success("✅ Relatório gerado com sucesso!")
                    
                    # Botão para download
                    st.download_button(
                        label="📥 Baixar Relatório PDF",
                        data=pdf_buffer.getvalue(),
                        file_name=f"relatorio_performance_{mes_referencia.lower()}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
        else:
            st.info("ℹ️ Carregue os dados do mês atual na aba 'Análise de Campanhas' para gerar o relatório PDF")
    
    with tab_relatorios:
        st.subheader("Meus Relatórios Gerados")
        
        relatorios = obter_relatorios_usuario(usuario.get("_id")) if usuario else []
        
        if relatorios:
            st.write(f"📚 Você tem {len(relatorios)} relatórios salvos:")
            
            # Adicionar funcionalidade de combinar relatórios com IA
            if len(relatorios) >= 2:
                st.subheader("🧠 Combinar Relatórios com IA")
                st.info("Selecione dois relatórios para criar uma análise integrada com IA")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    relatorio1_id = st.selectbox(
                        "Selecione o primeiro relatório",
                        options=[str(r["_id"]) for r in relatorios],
                        format_func=lambda x: next((f"{r.get('titulo', r.get('cliente', {}).get('nome', 'Sem nome'))} - {r.get('tipo', 'Sem tipo')} - {r['data_geracao'].strftime('%d/%m/%Y')}" for r in relatorios if str(r["_id"]) == x), "Relatório"),
                        key="combinar_1"
                    )
                
                with col2:
                    # Filtrar para não selecionar o mesmo relatório duas vezes
                    opcoes_relatorio2 = [str(r["_id"]) for r in relatorios if str(r["_id"]) != relatorio1_id]
                    relatorio2_id = st.selectbox(
                        "Selecione o segundo relatório",
                        options=opcoes_relatorio2,
                        format_func=lambda x: next((f"{r.get('titulo', r.get('cliente', {}).get('nome', 'Sem nome'))} - {r.get('tipo', 'Sem tipo')} - {r['data_geracao'].strftime('%d/%m/%Y')}" for r in relatorios if str(r["_id"]) == x), "Relatório"),
                        key="combinar_2"
                    )
                
                if st.button("🧠 Combinar com IA", type="primary"):
                    with st.spinner("Combinando relatórios com IA..."):
                        relatorio_id, mensagem = combinar_relatorios_com_llm(
                            relatorio1_id, 
                            relatorio2_id, 
                            usuario.get("_id")
                        )
                        
                        if relatorio_id:
                            st.success(mensagem)
                            # Mostrar o relatório combinado imediatamente
                            relatorio_combinado = obter_relatorio_completo(relatorio_id)
                            if relatorio_combinado:
                                for parte in relatorio_combinado.get("partes", []):
                                    with st.expander(f"**{parte['titulo']}**"):
                                        st.markdown(parte['conteudo'])
                            
                            st.rerun()
                        else:
                            st.error(mensagem)
            
            # Lista de relatórios existente...
            for rel in relatorios:
                # Usar o título gerado automaticamente se disponível, caso contrário usar o formato antigo
                titulo_relatorio = rel.get('titulo', f"{rel.get('cliente', {}).get('nome', 'Sem nome')} - {rel.get('tipo', 'Sem tipo')}")
                
                with st.expander(f"📄 {titulo_relatorio} - {rel['data_geracao'].strftime('%d/%m/%Y %H:%M')}"):                        
                    relatorio_completo = obter_relatorio_completo(rel["_id"])
                    if relatorio_completo:
                            for parte in relatorio_completo.get("partes", []):
                                st.markdown(f"### {parte['titulo']}")
                                st.markdown(parte['conteudo'])
                    
                    texto_completo = "\n\n".join([f"## {p['titulo']}\n\n{p['conteudo']}" for p in rel.get("partes", [])])
                    
                    # Gerar nome do arquivo para download baseado no título do relatório
                    nome_arquivo = rel.get('titulo', f"relatorio_{rel.get('tipo', 'geral')}_{rel['data_geracao'].strftime('%Y%m%d')}")
                    
                    st.download_button(
                        label="⬇️ Baixar Relatório",
                        data=texto_completo,
                        file_name=f"{nome_arquivo}.md",
                        mime="text/markdown",
                        key=f"download_{rel['_id']}"
                    )
                    
                    if st.button("🗑️ Excluir", key=f"excluir_{rel['_id']}"):
                        db_relatorios.update_one(
                            {"_id": rel["_id"]},
                            {"$set": {"status": "excluido"}}
                        )
                        st.success("Relatório marcado como excluído")
                        st.rerun()
        else:
            st.info("Você ainda não gerou nenhum relatório. Use a aba de análise para criar seu primeiro relatório.")
    
    with tab_planejamento:
        mostrar_planejamento_midia()

def main():
    """Função principal que controla o fluxo do aplicativo"""
    if not st.session_state.get("autenticado", False):
        mostrar_tela_login()
    else:
        mostrar_app_principal()

if __name__ == "__main__":
    main()
