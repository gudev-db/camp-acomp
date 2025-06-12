import streamlit as st
from .frontend.auth import mostrar_tela_login
from .frontend.dashboard import mostrar_app_principal

def main():
    """Função principal que controla o fluxo do aplicativo"""
    st.set_page_config(
        layout="wide",
        page_title="Analytics de Campanhas",
        page_icon="📊"
    )
    
    if not st.session_state.get("autenticado", False):
        mostrar_tela_login()
    else:
        mostrar_app_principal()

if __name__ == "__main__":
    main()
