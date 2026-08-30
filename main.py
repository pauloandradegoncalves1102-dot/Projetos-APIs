import os
from tkinter.filedialog import askdirectory

caminho = askdirectory(title="selecione uma Pasta")
print(caminho)

lista_arquivos = os.listdir(caminho)

locais = {
    "imagens": [".pmg", ".jpg"],
    "planilhas": [".xlsx"],
    "pdfs": [".pdf"],
    "csv": [".csv"],
}

for arquivo in lista_arquivos:
    nome, extensão = os.path.splitext(f"{caminho}/{arquivo}")
    for pasta in locais:
        if extensão in locais[pasta]:
            if not os.path.exists(f"{caminho}/{pasta}"):
                os.mkdir(f"{caminho}/{pasta}")
            os.rename(f"caminho/{arquivo}", f"{caminho}/{pasta}/{arquivo}")    
