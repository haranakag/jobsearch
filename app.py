import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime

# --- CONFIGURAÇÃO: SEUS ALVOS ---
CARGOS_FIXOS = [
    "DevOps",
    "SRE",
    "Site Reliability Engineer",
    "Cloud Engineer",
    "Platform Engineer",
    "Infrastructure Engineer",
    "Engenheiro de Dados",
    "Solutions Architect"
]

def limpar_texto(texto):
    """Remove espaços extras e quebras de linha."""
    if texto:
        return " ".join(texto.split()).lower()
    return ""

def analisar_url_rigoroso(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0'
    }
    
    resultado = {
        "URL": url,
        "Status": "Erro",
        "Cargo Principal": "❌ Não encontrado no Título", # Padrão negativo
        "Confiança": "Baixa",
        "Modelo": [],
        "Latam": False
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. LIMPEZA ESTRUTURAL (CRUCIAL PARA EVITAR FALSOS POSITIVOS)
            # Removemos menus, rodapés, sidebars e scripts antes de ler.
            # Isso evita ler "DevOps" num link de "Outras vagas" no rodapé.
            for tag in soup(["script", "style", "nav", "footer", "aside", "noscript"]):
                tag.decompose()

            resultado["Status"] = "✅ Lido"
            
            # --- FILTRO 1: O CARGO (Busca Restrita) ---
            # Só aceita se estiver no Título da Aba (<title>) ou no Título da Página (h1, h2)
            titulo_aba = limpar_texto(soup.title.string) if soup.title else ""
            
            # Pega todos os h1 e h2
            headers_text = " ".join([limpar_texto(h.get_text()) for h in soup.find_all(['h1', 'h2'])])
            
            # Texto onde procuraremos o cargo (Apenas títulos!)
            area_nobre = titulo_aba + " " + headers_text
            
            cargos_encontrados = []
            for cargo in CARGOS_FIXOS:
                # Verificação de palavra inteira ou parte forte
                if cargo.lower() in area_nobre:
                    cargos_encontrados.append(cargo)
            
            if cargos_encontrados:
                resultado["Cargo Principal"] = ", ".join(list(set(cargos_encontrados)))
                resultado["Confiança"] = "Alta (Está no Título)"
            
            # --- FILTRO 2: DETALHES (Busca no Corpo Limpo) ---
            # Agora lemos o corpo, mas lembre-se: já removemos rodapés e menus.
            corpo_limpo = limpar_texto(soup.get_body_text() if hasattr(soup, 'get_body_text') else soup.get_text())
            
            # Modelo
            if "remote" in corpo_limpo or "remoto" in corpo_limpo: resultado["Modelo"].append("Remoto")
            if "hybrid" in corpo_limpo or "híbrido" in corpo_limpo: resultado["Modelo"].append("Híbrido")
            if "on-site" in corpo_limpo or "presencial" in corpo_limpo: resultado["Modelo"].append("Presencial")
            
            # Latam
            termos_latam = ["latam", "latin america", "américa latina", "south america"]
            if any(t in corpo_limpo for t in termos_latam):
                resultado["Latam"] = True
                
        else:
            resultado["Status"] = f"Erro HTTP {response.status_code}"

    except Exception as e:
        resultado["Status"] = "Falha Conexão"

    # Formatação final
    resultado["Modelo"] = ", ".join(resultado["Modelo"]) if resultado["Modelo"] else "Não especificado"
    
    return resultado

# --- INTERFACE ---
st.set_page_config(page_title="Validador Rigoroso", layout="wide")
st.title("🛡️ Validador de Vagas (Modo Rigoroso)")
st.markdown("""
Este modo **ignora** rodapés, menus e links laterais. 
Ele só considera que a vaga é válida se o Cargo estiver no **Título** ou **Cabeçalho (H1/H2)** da página.
""")

urls_input = st.text_area("URLs para análise rigorosa:", height=200)

if st.button("🔍 Analisar com Rigor"):
    urls_lista = [u.strip() for u in urls_input.split('\n') if u.strip()]

    if urls_lista:
        progresso = st.progress(0)
        dados = []
        
        for i, url in enumerate(urls_lista):
            d = analisar_url_rigoroso(url)
            dados.append(d)
            progresso.progress((i + 1) / len(urls_lista))
            time.sleep(0.5)
            
        progresso.empty()
        
        df = pd.DataFrame(dados)
        
        # Filtro Visual: Mostra primeiro o que deu match
        df = df.sort_values(by="Confiança", ascending=True) 

        st.dataframe(
            df,
            column_config={
                "URL": st.column_config.LinkColumn("Link"),
                "Latam": st.column_config.CheckboxColumn("Latam?"),
                "Status": st.column_config.TextColumn("Status Leitura")
            },
            use_container_width=True
        )
    else:
        st.warning("Insira URLs.")
