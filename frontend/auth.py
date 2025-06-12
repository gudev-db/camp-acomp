import streamlit as st
import time
from ..services.auth_service import AuthService

def mostrar_tela_login():
    """Mostra a tela de login/cadastro"""
    st.title("🔐 Login / Cadastro")
    auth_service = AuthService()
    
    tab_login, tab_cadastro = st.tabs(["Login", "Cadastro"])
    
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            senha = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar")
            
            if submit:
                sucesso, usuario, mensagem = auth_service.verificar_login(email, senha)
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
                    sucesso, mensagem = auth_service.criar_usuario(email_cadastro, senha_cadastro, nome)
                    if sucesso:
                        st.success(mensagem)
                    else:
                        st.error(mensagem)
