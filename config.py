import os

class Config:
    MONGO_URI = "mongodb+srv://gustavoromao3345:RqWFPNOJQfInAW1N@cluster0.5iilj.mongodb.net/auto_doc?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE&tlsAllowInvalidCertificates=true"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    DATABASE_NAME = "arquivos_planejamento"
    COLLECTIONS = {
        "clientes": "clientes",
        "usuarios": "usuarios",
        "relatorios": "relatorios"
    }
