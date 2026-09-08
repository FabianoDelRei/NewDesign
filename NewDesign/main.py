import os
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr

app = FastAPI(title="API Salão de Luxo - NewDesign")

# 1. Criação automática de diretórios
os.makedirs("uploads", exist_ok=True)
os.makedirs("static", exist_ok=True)

# 2. Configuração de arquivos estáticos (HTML, fotos)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

# 3. Simulação de Banco de Dados em Memória
usuarios_db = []
fila_atendimento = [
    {"id": 1, "nome": "Maria Silva", "funcao": "Manicure", "posicao": 1, "status": "LIVRE", "salao": "ITAIM", "atendimentos": 5, "valor_bruto": 500.0, "desconto": 50.0},
    {"id": 2, "nome": "Ana Costa", "funcao": "Cabeleireira", "posicao": 2, "status": "OCUPADA", "salao": "MORUMBI", "atendimentos": 8, "valor_bruto": 1200.0, "desconto": 100.0},
    {"id": 3, "nome": "Carla Souza", "funcao": "Esteticista", "posicao": 3, "status": "ALMOÇO", "salao": "ITAIM", "atendimentos": 3, "valor_bruto": 450.0, "desconto": 20.0}
]

SERVICOS = [
    "MANICURE", "PEDICURE", "MANICURE E PEDICURE", "BANHO DE GEL", 
    "EXTENSÃO DE UNHA", "ESMALTAÇÃO", "ESMALTAÇÃO DE GEL", 
    "CABELO", "LUZES", "CORTE", "PINTURA"
]

# 4. Modelos de Dados (Schemas de Entrada)
class UsuarioCreate(BaseModel):
    nome: str
    sobrenome: str
    rg: str
    cpf: str
    data_nascimento: str
    funcao: str
    email: EmailStr
    senha: str
    salao: str  # MORUMBI ou ITAIM

class Agendamento(BaseModel):
    cliente_nome: str
    profissional_id: int
    servico: str
    hora_marcada: Optional[str] = None

# 5. Rotas da Aplicação

# Rota Principal: Serve a interface web (index.html)
@app.get("/")
def home():
    return FileResponse("static/index.html")

# Lista os serviços disponíveis no salão
@app.get("/servicos")
def listar_servicos():
    return SERVICOS

# Cadastro de novo colaborador
@app.post("/auth/cadastro")
def cadastrar_usuario(user: UsuarioCreate):
    if user.salao not in ["MORUMBI", "ITAIM"]:
        raise HTTPException(status_code=400, detail="Salão inválido. Escolha MORUMBI ou ITAIM.")
    usuarios_db.append(user.model_dump())
    return {"mensagem": "Usuário cadastrado com sucesso!"}

# Consulta a fila ordenada por posição
@app.get("/fila")
def ver_fila():
    return sorted(fila_atendimento, key=lambda x: x["posicao"])

# Recepção agenda serviço para cliente
@app.post("/atendimento/agendar")
def agendar_servico(agendamento: Agendamento):
    prof = next((p for p in fila_atendimento if p["id"] == agendamento.profissional_id), None)
    if not prof:
        raise HTTPException(status_code=404, detail="Profissional não encontrada")
    
    prof["status"] = "OCUPADA"
    return {"mensagem": f"Serviço {agendamento.servico} agendado para {agendamento.cliente_nome} com {prof['nome']}"}

# Finalização de atendimento com foto e reordenação da fila
@app.post("/atendimento/finalizar/{profissional_id}")
async def finalizar_atendimento(
    profissional_id: int, 
    cliente_nome: str = Form(...),
    foto: UploadFile = File(...)
):
    prof = next((p for p in fila_atendimento if p["id"] == profissional_id), None)
    if not prof:
        raise HTTPException(status_code=404, detail="Profissional não encontrada")
    
    # Salva o arquivo de imagem enviado na pasta uploads/
    caminho_foto = f"uploads/{datetime.now().timestamp()}_{foto.filename}"
    with open(caminho_foto, "wb") as f:
        f.write(await foto.read())
        
    # Move quem finalizou para o final da fila e avança os demais
    max_posicao = max(p["posicao"] for p in fila_atendimento)
    for p in fila_atendimento:
        if p["id"] == profissional_id:
            p["posicao"] = max_posicao
            p["status"] = "LIVRE"
        else:
            p["posicao"] -= 1
            
    return {
        "mensagem": "Atendimento finalizado!",
        "cliente": cliente_nome,
        "foto_url": caminho_foto,
        "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# Relatório financeiro exclusivo para gestão
@app.get("/admin/relatorio")
def relatorio_financeiro(cargo: str):
    if cargo.upper() not in ["DONA", "GERENTE"]:
        raise HTTPException(status_code=403, detail="Acesso restrito para Dona e Gerente.")
    
    relatorio = []
    for prof in sorted(fila_atendimento, key=lambda x: x["nome"]):
        bruto = prof["valor_bruto"]
        comissao = bruto * 0.50  # Regra de negócio: 50% de repasse
        desconto = prof["desconto"]
        liquido = comissao - desconto
        
        relatorio.append({
            "nome": prof["nome"],
            "funcao": prof["funcao"],
            "status": prof["status"],
            "atendimentos": prof["atendimentos"],
            "valor_bruto": bruto,
            "pagamento_colaborador": comissao,
            "desconto": desconto,
            "valor_liquido": liquido
        })
    return relatorio

# Alteração de status (Bloqueio / Liberação / Almoço)
@app.patch("/admin/bloquear-colaborador/{profissional_id}")
def alterar_status_bloqueio(profissional_id: int, status: str, cargo: str):
    if cargo.upper() not in ["DONA", "GERENTE"]:
        raise HTTPException(status_code=403, detail="Acesso não autorizado.")
    
    prof = next((p for p in fila_atendimento if p["id"] == profissional_id), None)
    if not prof:
        raise HTTPException(status_code=404, detail="Profissional não encontrada")
    
    prof["status"] = status
    return {"mensagem": f"Status atualizado para {status}"}