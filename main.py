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

# Configuração da página
st.set_page_config(
    layout="wide",
    page_title="Analytics de Campanhas",
    page_icon="📊"
)

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
            *O que é:* Anúncios visuais em sites parceiros do Google.  
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
db_clientes = banco["clientes"]  # info clientes
db_usuarios = banco["usuarios"]  # coleção para usuários
db_relatorios = banco["relatorios"]  # coleção específica para relatórios

# Verifica se a API key do Gemini está configurada
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    st.warning("⚠️ Chave da API Gemini não encontrada. O relatório avançado será limitado.")

# Funções do aplicativo ==============================================

def criar_usuario(email, senha, nome):
    """Cria um novo usuário no banco de dados"""
    # Verifica se o usuário já existe
    if db_usuarios.find_one({"email": email}):
        return False, "Usuário já existe"
    
    # Cria hash da senha
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    
    # Insere o novo usuário
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
        # Atualiza último login
        db_usuarios.update_one(
            {"_id": usuario["_id"]},
            {"$set": {"ultimo_login": datetime.now()}}
        )
        return True, usuario, "Login bem-sucedido"
    else:
        return False, None, "Senha incorreta"

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

# Função para detectar etapa do funil pelo nome da campanha
def detectar_etapa_funil(nome_campanha):
    nome = nome_campanha.lower()
    
    # Palavras-chave para cada etapa
    topo_keywords = ['awareness', 'consciencia', 'alcance', 'reach', 'branding', 'marca']
    meio_keywords = ['consideracao', 'consideração', 'consideration', 'engajamento', 'engagement', 'video', 'vídeo']
    fundo_keywords = ['conversao', 'conversão', 'conversion', 'venda', 'sales', 'lead', 'performance', 'pmax']
    
    if any(keyword in nome for keyword in topo_keywords):
        return 'Topo'
    elif any(keyword in nome for keyword in meio_keywords):
        return 'Meio'
    elif any(keyword in nome for keyword in fundo_keywords):
        return 'Fundo'
    else:
        return 'Outros'

# Métricas por etapa do funil
METRICAS_POR_ETAPA = {
    'Topo': ['Impressões', 'Alcance', 'Custo', 'CPM médio', 'Cliques', 'CTR'],
    'Meio': ['Impressões', 'Cliques', 'CTR', 'CPC médio', 'CPM médio', 'Custo'],
    'Fundo': ['Impressões', 'Cliques', 'Conversões', 'CTR', 'CPM médio', 'CPC médio', 'Custo por conversão']
}

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
            {"titulo": 1, "data_geracao": 1, "tipo": 1, "cliente.nome": 1}
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

def gerar_relatorio_llm(df, metricas, colunas_selecionadas, tipo_relatorio, cliente_info=None, df_anterior=None, usuario_id=None):
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
        for col in colunas_selecionadas[:10]:  # Limita a 3 métricas para não ficar muito longo
            if col in df.columns:
                top3 = df.nlargest(10, col)[['Campanha', col]]
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

                    Dê apenas um panorama geral sobre os dados com os pontos:

                    - Visão geral do desempenho das campanhas
                    - Contexto sobre os dados analisados
                    - Destaque inicial dos pontos mais relevantes
                    
                    Dados: {dados_para_llm}
                    
                    """),
                    ("2. Análise de cada métrica selecionada", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}

                    Faça apenas uma análise técnica detalhada de cada métrica selecionada, com os pontos:
                    - Significado de cada métrica
                    - Performance em relação aos benchmarks do setor
                    - Relação com o tipo de campanha
                    
                    Dados: {dados_para_llm}
 
                    """),
                    ("3. Comparativo mensal detalhado", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    - Considere os objetivos das campanhas (que podem ser deduzidos pelos seus nomes) quando fizer sua análise
                    Faça apenas um comparativo mensal detalhado com os pontos:
                    Analise comparativamente os dados com o mês anterior (quando disponível):
                    - Variações percentuais significativas
                    - Tendências identificadas
                    
                    Dados: {dados_para_llm}

                    """),
                    ("4. Insights sobre correlações", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    - Considere os objetivos das campanhas (que podem ser deduzidos pelos seus nomes) quando fizer sua análise
                
                    Apenas Identifique correlações importantes entre as métricas com os pontos:
                    - Relações causa-efeito
                    - Padrões de desempenho
                    - Anomalias e outliers
                    - EX: Se métrica X subiu e métrica Y abaixou, isso significa que...
                    
                    Dados: {dados_para_llm}
        
                    """),
                    ("5. Recomendações técnicas", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    - Considere os objetivos das campanhas (que podem ser deduzidos pelos seus nomes) quando fizer sua análise
                    Apenas gere recomendações técnicas específicas baseadas na análise com os pontos:
                    - Ajustes em campanhas
                    - Otimizações sugeridas
                    - Alertas sobre problemas identificados
                    
                    Dados: {dados_para_llm}
 
                    """),
                    ("6. Conclusão com resumo executivo", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    - Considere os objetivos das campanhas (que podem ser deduzidos pelos seus nomes) quando fizer sua análise
                    Apenas Conclua com um resumo executivo técnico com os pontos:
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
                    - Considere os objetivos das campanhas (que podem ser deduzidos pelos seus nomes) quando fizer sua análise
                    Você é um estrategista de marketing. Apenas Gere uma visão geral simplificada em português com os pontos:
                    - Principais resultados
                    - Destaques e preocupações
                    - Contexto estratégico
                    
                    Dados: {dados_para_llm}
        
                    """),
                    ("2. Principais destaques e preocupações", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    - Considere os objetivos das campanhas (que podem ser deduzidos pelos seus nomes) quando fizer sua análise
                    Destaque os pontos mais relevantes e preocupações:

                    Apenas apresente os principais destaques e preocupações com os pontos:
                    - Comparações mensais
                    - Variações significativas
                    - Impacto estratégico dado o tipo de campanha
                    - Alinhamento com objetivos dado o tipo de campanha
                    
                    Dados: {dados_para_llm}

                    """),
                    ("3. Análise estratégica do desempenho", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    - Considere os objetivos das campanhas (que podem ser deduzidos pelos seus nomes) quando fizer sua análise
                    Apenas Analise o desempenho com foco em tendências com os pontos:
                    - Padrões de longo prazo
                    - Eficácia estratégica
                    - Alinhamento com objetivos dado o tipo de campanha
                    
                    Dados: {dados_para_llm}

                    """),
                    ("4. Relações entre métricas", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    - Considere os objetivos das campanhas (que podem ser deduzidos pelos seus nomes) quando fizer sua análise

                    Apenas Explique como as métricas se relacionam e impactam os resultados com os pontos:
                    - Conexões importantes
                    - Trade-offs identificados
                    - Sinergias encontradas
                    - Relações causa-efeito
                    - Tire insights sobre os trade offs entre as variações das métricas. Relacione-as e tire conclusões sobre o que está acontecendo.
                    
                    Dados: {dados_para_llm}

                    """),
                    ("5. Recomendações de alto nível", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    - Considere os objetivos das campanhas (que podem ser deduzidos pelos seus nomes) quando fizer sua análise
                    Apenas Gere recomendações estratégicas com os pontos:
                    - Direcionamentos gerais
                    - Priorizações sugeridas
                    - Ajustes recomendados
                    
                    Dados: {dados_para_llm}

                    """),
                    ("6. Próximos passos sugeridos", f"""
                    - Quando mencionar métricas, considere o enfoque métrica vs tipo de campanha: {rel_metrica}
                    - Considere os objetivos das campanhas (que podem ser deduzidos pelos seus nomes) quando fizer sua análise
                    Apenas Defina os próximos passos estratégicos com os pontos:
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
            relatorio_id = salvar_relatorio_mongodb(relatorio_data, usuario_id)
            if relatorio_id:
                st.success("✅ Relatório salvo no banco de dados com sucesso!")
            
            return relatorio_completo
        
    except Exception as e:
        return {
            "partes": [{"titulo": "Erro", "conteudo": f"Erro ao gerar relatório: {str(e)}"}],
            "texto_completo": f"Erro ao gerar relatório: {str(e)}"
        }

# Sistema de Autenticação ============================================

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
                else:
                    sucesso, mensagem = criar_usuario(email_cadastro, senha_cadastro, nome)
                    if sucesso:
                        st.success(mensagem)
                    else:
                        st.error(mensagem)

def mostrar_app_principal():
    """Mostra o aplicativo principal após o login"""
    usuario = st.session_state.get("usuario", {})
    
    # Barra lateral com informações do usuário
    with st.sidebar:
        st.markdown(f"### 👤 {usuario.get('nome', 'Usuário')}")
        st.markdown(f"✉️ {usuario.get('email', '')}")
        
        if st.button("🚪 Sair"):
            del st.session_state["usuario"]
            del st.session_state["autenticado"]
            st.rerun()
    
    # Título principal
    st.title("📊 Analytics Avançado de Campanhas Digitais")
    
    # Sessão para armazenar os dados carregados
    if 'dados_atual' not in st.session_state:
        st.session_state.dados_atual = None
        st.session_state.dados_anterior = None
    
    # Abas principais
    tab_analise, tab_relatorios = st.tabs(["📈 Análise de Campanhas", "🗂 Meus Relatórios"])
    
    with tab_analise:
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
                    # Adiciona colunas de tipo detectado e etapa do funil
                    df_atual['Tipo Detectado'] = df_atual['Campanha'].apply(detectar_tipo_campanha)
                    df_atual['Etapa Funil'] = df_atual['Campanha'].apply(detectar_etapa_funil)
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
                    # Adiciona colunas de tipo detectado e etapa do funil
                    df_anterior['Tipo Detectado'] = df_anterior['Campanha'].apply(detectar_tipo_campanha)
                    df_anterior['Etapa Funil'] = df_anterior['Campanha'].apply(detectar_etapa_funil)
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
                
                # Filtro por etapa do funil
                etapas_disponiveis = sorted(df['Etapa Funil'].unique())
                etapas_funil = st.multiselect(
                    "Etapa do Funil",
                    options=etapas_disponiveis,
                    default=etapas_disponiveis
                )
                
                # Métricas relevantes para as etapas selecionadas
                METRICAS_POR_ETAPA = {
                    'Topo': ['Impressões', 'Alcance', 'Custo', 'CPM médio', 'Cliques', 'CTR'],
                    'Meio': ['Impressões', 'Cliques', 'CTR', 'CPC médio', 'CPM médio', 'Custo'],
                    'Fundo': ['Impressões', 'Cliques', 'Conversões', 'CTR', 'CPM médio', 'CPC médio', 'Custo por conversão']
                }
                
                # Seleciona métricas baseadas na etapa do funil
                metricas_selecionadas = []
                for etapa in etapas_funil:
                    metricas_selecionadas.extend(METRICAS_POR_ETAPA.get(etapa, []))
                
                # Remove duplicatas e mantém apenas métricas existentes no dataframe
                metricas_selecionadas = [m for m in list(set(metricas_selecionadas)) if m in df.columns]
                
                # Tipo de relatório
                tipo_relatorio = st.radio(
                    "Tipo de relatório",
                    options=["técnico", "gerencial"],
                    index=0
                )
                
                # Filtros adicionais
                st.subheader("Filtros Adicionais")
                
                # Filtro por tipo detectado
                tipos_detectados = sorted(df['Tipo Detectado'].unique())
                tipos_selecionados = st.multiselect(
                    "Tipo de Campanha (detectado pelo nome)",
                    options=tipos_detectados,
                    default=tipos_detectados
                )
                
                # Filtro por tipo de campanha
                tipos_campanha = sorted(df['Tipo de campanha'].unique())
                tipo_campanha = st.multiselect(
                    "Tipo de Campanha (do relatório)",
                    options=tipos_campanha,
                    default=tipos_campanha
                )
                
                # Filtro por status da campanha
                status_disponiveis = sorted(df['Status da campanha'].unique())
                status_campanha = st.multiselect(
                    "Status da Campanha",
                    options=status_disponiveis,
                    default=['Ativa'] if 'Ativa' in status_disponiveis else status_disponiveis
                )
                
                mostrar_boxplots = st.checkbox("Mostrar boxplots das métricas")
            
            # Aplica filtros
            df_filtrado = df[
                (df['Etapa Funil'].isin(etapas_funil)) &
                (df['Tipo Detectado'].isin(tipos_selecionados)) &
                (df['Tipo de campanha'].isin(tipo_campanha)) &
                (df['Status da campanha'].isin(status_campanha))
            ].copy()
            
            # Contagem correta de campanhas ativas e pausadas
            contagem_ativas = len(df_filtrado[df_filtrado['Status da campanha'] == 'Ativada'])
            contagem_pausadas = len(df_filtrado[df_filtrado['Status da campanha'] == 'Pausada'])
            
            # Sub-abas de análise
            tab1, tab2, tab3, tab4 = st.tabs(["📋 Visão Geral", "📊 Análise por Métrica", "🔄 Comparativo Mensal", "🧠 Relatório Avançado"])
            
            with tab1:
                st.subheader("Visão Geral das Campanhas - Mês Atual")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total de Campanhas", len(df_filtrado))
                col2.metric("Campanhas Ativas", contagem_ativas)
                col3.metric("Campanhas Pausadas", contagem_pausadas)
                
                # Mostra distribuição por etapa do funil
                st.subheader("Distribuição por Etapa do Funil")
                fig, ax = plt.subplots(figsize=(8, 4))
                df_filtrado['Etapa Funil'].value_counts().plot(kind='bar', ax=ax, color=['#4CAF50', '#2196F3', '#FF9800'])
                plt.title('Campanhas por Etapa do Funil')
                plt.xlabel('Etapa do Funil')
                plt.ylabel('Número de Campanhas')
                st.pyplot(fig)
                
                # Mostra dataframe com as métricas relevantes
                st.dataframe(df_filtrado[['Campanha', 'Etapa Funil', 'Tipo Detectado', 'Status da campanha'] + metricas_selecionadas], 
                            use_container_width=True)
            
            with tab2:
                st.subheader("Análise Detalhada por Métrica - Mês Atual")
                
                metrica_selecionada = st.selectbox(
                    "Selecione uma métrica para análise detalhada",
                    options=metricas_selecionadas
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
                    
                    st.subheader(f"Top 5 Campanhas - {metrica_selecionada}")
                    top5 = df_filtrado.nlargest(5, metrica_selecionada)[['Campanha', 'Etapa Funil', metrica_selecionada]]
                    st.dataframe(top5.style.format({metrica_selecionada: "{:,.2f}"}))
                    
                    st.subheader(f"Bottom 5 Campanhas - {metrica_selecionada}")
                    bottom5 = df_filtrado.nsmallest(5, metrica_selecionada)[['Campanha', 'Etapa Funil', metrica_selecionada]]
                    st.dataframe(bottom5.style.format({metrica_selecionada: "{:,.2f}"}))
            
            with tab3:
                st.subheader("Comparativo Mensal")
                
                if st.session_state.dados_anterior is not None:
                    # Aplica os mesmos filtros ao mês anterior
                    df_anterior_filtrado = st.session_state.dados_anterior[
                        (st.session_state.dados_anterior['Etapa Funil'].isin(etapas_funil)) &
                        (st.session_state.dados_anterior['Tipo Detectado'].isin(tipos_selecionados)) &
                        (st.session_state.dados_anterior['Tipo de campanha'].isin(tipo_campanha)) &
                        (st.session_state.dados_anterior['Status da campanha'].isin(status_campanha))
                    ]
                    
                    metrica_comparacao = st.selectbox(
                        "Selecione uma métrica para comparação",
                        options=metricas_selecionadas,
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
                    relatorio = gerar_relatorio_llm(
                        df_filtrado, 
                        metricas, 
                        metricas_selecionadas,  # Usa apenas as métricas relevantes para o funil
                        tipo_relatorio, 
                        cliente_info,
                        st.session_state.dados_anterior if st.session_state.dados_anterior is not None else None,
                        usuario.get("_id")
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
        else:
            st.info("ℹ️ Por favor, carregue pelo menos o relatório do mês atual para começar a análise")
    
    with tab_relatorios:
        st.subheader("Meus Relatórios Gerados")
        
        # Obtém os relatórios do usuário
        relatorios = obter_relatorios_usuario(usuario.get("_id"))
        
        if relatorios:
            st.write(f"📚 Você tem {len(relatorios)} relatórios salvos:")
            
            for rel in relatorios:
                with st.expander(f"📄 {rel.get('cliente', {}).get('nome', 'Sem nome')} - {rel.get('tipo', 'Sem tipo')} - {rel['data_geracao'].strftime('%d/%m/%Y %H:%M')}"):
                    # Botão para visualizar o relatório completo
                    if st.button("🔍 Ver Relatório Completo", key=f"ver_{rel['_id']}"):
                        relatorio_completo = obter_relatorio_completo(rel["_id"])
                        if relatorio_completo:
                            for parte in relatorio_completo.get("partes", []):
                                st.markdown(f"### {parte['titulo']}")
                                st.markdown(parte['conteudo'])
                    
                    # Botão para download
                    texto_completo = "\n\n".join([f"## {p['titulo']}\n\n{p['conteudo']}" for p in rel.get("partes", [])])
                    st.download_button(
                        label="⬇️ Baixar Relatório",
                        data=texto_completo,
                        file_name=f"relatorio_{rel.get('tipo', 'geral')}_{rel['data_geracao'].strftime('%Y%m%d')}.md",
                        mime="text/markdown",
                        key=f"download_{rel['_id']}"
                    )
                    
                    # Botão para excluir
                    if st.button("🗑️ Excluir", key=f"excluir_{rel['_id']}"):
                        db_relatorios.update_one(
                            {"_id": rel["_id"]},
                            {"$set": {"status": "excluido"}}
                        )
                        st.success("Relatório marcado como excluído")
                        st.rerun()
        else:
            st.info("Você ainda não gerou nenhum relatório. Use a aba de análise para criar seu primeiro relatório.")

# Ponto de entrada do aplicativo =====================================

def main():
    """Função principal que controla o fluxo do aplicativo"""
    if not st.session_state.get("autenticado", False):
        mostrar_tela_login()
    else:
        mostrar_app_principal()

if __name__ == "__main__":
    main()
