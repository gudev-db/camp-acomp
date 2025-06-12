import pandas as pd
import numpy as np

class DataService:
    @staticmethod
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
            raise Exception(f"Erro ao carregar arquivo: {str(e)}")
    
    @staticmethod
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
    
    @staticmethod
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
