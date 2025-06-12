import hashlib
from datetime import datetime
from ..utils.config import Config
from ..services.mongo_service import MongoService

class AuthService:
    def __init__(self):
        self.mongo = MongoService(Config.MONGO_URI, Config.DATABASE_NAME)
    
    def criar_usuario(self, email, senha, nome):
        """Cria um novo usuário no banco de dados"""
        if self.mongo.find_one("usuarios", {"email": email}):
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
            self.mongo.insert_one("usuarios", novo_usuario)
            return True, "Usuário criado com sucesso"
        except Exception as e:
            return False, f"Erro ao criar usuário: {str(e)}"
    
    def verificar_login(self, email, senha):
        """Verifica as credenciais do usuário"""
        usuario = self.mongo.find_one("usuarios", {"email": email})
        
        if not usuario:
            return False, None, "Usuário não encontrado"
        
        if not usuario.get("ativo", True):
            return False, None, "Usuário desativado"
        
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        
        if usuario["senha"] == senha_hash:
            self.mongo.update_one(
                "usuarios",
                {"_id": usuario["_id"]},
                {"$set": {"ultimo_login": datetime.now()}}
            )
            return True, usuario, "Login bem-sucedido"
        else:
            return False, None, "Senha incorreta"
