import requests

url = "https://economia.awesomeapi.com.br/json/last/USD-BRL"

resposta = requests.get(url)
print(resposta)

if resposta.status_code == 200:
    dados = resposta.json()         

    print(dados)

    dolar = dados["USDBRL"]         

    compra = float(dolar["bid"])
    venda = float(dolar["ask"])

    print(f"COMPRA: R$ {compra:.2f}")
    print(f"VENDA:  R$ {venda:.2f}")  

    valor = float(input("Digite o valor em USD: "))

    convertido = valor * venda

    print(f"U$ {valor:.2f} = R$ {convertido:.2f}")   
