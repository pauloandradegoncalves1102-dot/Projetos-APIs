from fastapi import FastAPI

app = FastAPI()

vendas = {
    1:{"Item": "Lata", "preco_unitario": 4, "quantidade":5},
    2:{"Item": "garrafa 2L", "preco_unitario": 15, "quantidade":5},
    3:{"Item": "garrafa 750ml", "preco_unitario": 10, "quantidade":5},
    4:{"Item": "Lata mini", "preco_unitario": 2, "quantidade":5},
}

@app.get("/")
def home():
    return {"Vendas": len(vendas)}

@app.get("/vendas/{id_vendas}")
def pegar_venda(id_vendas: int):
    return vendas[id_vendas]