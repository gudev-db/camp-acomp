    def generate_performance_summary(self, df, metrics):
        """Generate a performance summary table"""
        summary = {}
        for metric in metrics:
            summary[metric] = {
                'Média': df[metric].mean(),
                'Mediana': df[metric].median(),
                'Desvio Padrão': df[metric].std(),
                'Mínimo': df[metric].min(),
                'Máximo': df[metric].max()
            }
        return pd.DataFrame(summary).T
    
    def detect_anomalies(self, df, metric, threshold=2):
        """Detect anomalies in metric values"""
        z_scores = (df[metric] - df[metric].mean()) / df[metric].std()
        return df[np.abs(z_scores) > threshold]
