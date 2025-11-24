import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# --- CONFIGURAÇÃO: LISTA FIXA DE CARGOS ---
# O robô vai procurar por ESTES termos exatos dentro do site
CARGOS_FIXOS = [
    "DevOps Engineer",
    "DevOps",
    "Cloud Engineer",
    "Site Reliability Engineer",
    "SRE",
    "Platform Engineer",
    "Infrastructure Engineer",
    "Engenheiro de Dados" # Adicionei um extra como exemplo
]

# --- Função de Análise ---
def analisar_url(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0'}
    
    # Estrutura do resultado
    resultado = {
        "URL": url,
        "Status": "Erro",
        "Cargos Detectados": [],
        "Modelo": [],
        "Latam": False
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Limpeza de scripts e CSS
            for s in soup(["script", "style"]): s.extract()
            texto_pagina = soup.get_text().lower()
            
            resultado["Status"] = "✅ Lido"

            # 1. VERIFICAÇÃO DOS CARGOS FIXOS
            # Varre a lista fixa e vê se algum aparece no texto
            for cargo in CARGOS_FIXOS:
                if cargo.lower() in texto_pagina:
                    resultado["Cargos Detectados"].append(cargo)
            
            # Se a lista estiver vazia, marca como nenhum
            if not resultado["Cargos Detectados"]:
                resultado["Cargos Detectados"].append("Nenhum da lista")

            # 2. VERIFICAÇÃO DE MODELO
            if "remoto" in texto_pagina or "remote" in texto_pagina: resultado["Modelo"].append("Remoto")
            if "híbrido" in texto_pagina or "hybrid" in texto_pagina: resultado["Modelo"].append("Híbrido")
            if "presencial" in texto_pagina or "on-site" in texto_pagina: resultado["Modelo"].append("Presencial")

            # 3. VERIFICAÇÃO DE REGIÃO (LATAM)
            termos_latam = ["latam", "latin america", "américa latina", "south america"]
            if any(t in texto_pagina for t in termos_latam):
                resultado["Latam"] = True
                
        else:
            resultado["Status"] = f"Erro {response.status_code}"

    except Exception as e:
        resultado["Status"] = "Erro de Conexão"

    # Formatação final para a tabela
    resultado["Cargos Detectados"] = ", ".join(resultado["Cargos Detectados"])
    resultado["Modelo"] = ", ".join(resultado["Modelo"]) if resultado["Modelo"] else "Não especificado"
    
    return resultado

# --- Interface do App ---
st.set_page_config(page_title="Validador de Vagas", layout="wide")

st.title("🛡️ Validador de Vagas: Tech & Latam")
st.markdown("### Como funciona:")
st.markdown("1. O sistema já sabe que você busca: **DevOps, SRE, Cloud, Platform, Infra**.")
st.markdown("2. Você cola os links, e ele diz qual cargo encontrou lá dentro e se é LATAM.")

# Exibe a lista fixa para o usuário ter certeza
with st.expander("Ver lista fixa de cargos pesquisados"):
    st.write(CARGOS_FIXOS)

# Área de Texto
urls_input = st.text_area("Cole suas URLs aqui (uma por linha):", height=200)

if st.button("Analisar Lista"):
    urls_lista = [u.strip() for u in urls_input.split('\n') if u.strip()]

    if not urls_lista:
        st.warning("A lista está vazia.")
    else:
        # Barra de progresso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        dados_relatorio = []

        # Loop de processamento
        for i, url in enumerate(urls_lista):
            status_text.text(f"Verificando link {i+1} de {len(urls_lista)}...")
            
            dados = analisar_url(url)
            dados_relatorio.append(dados)
            
            progress_bar.progress((i + 1) / len(urls_lista))
            time.sleep(0.5) # Pausa amigável

        status_text.text("Concluído!")
        progress_bar.empty()

        # --- Exibição da Tabela ---
        st.divider()
        st.subheader("Resultado da Análise")

        df = pd.DataFrame(dados_relatorio)

        # Reordenar colunas
        colunas_ordem = ["Status", "Cargos Detectados", "Modelo", "Latam", "URL"]
        df = df[colunas_ordem]

        # Estilização da tabela
        st.dataframe(
            df,
            column_config={
                "URL": st.column_config.LinkColumn("Acessar Vaga"),
                "Latam": st.column_config.CheckboxColumn("É Latam?", default=False),
                "Cargos Detectados": st.column_config.TextColumn("Cargo(s) Encontrado(s)"),
            },
            use_container_width=True,
            hide_index=True
        )
