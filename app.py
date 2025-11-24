import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# --- Função de Scraping (Otimizada para Relatório) ---
def analisar_vaga(url, cargo_alvo):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0'}
    
    resultado = {
        "URL": url,
        "Status": "Erro/Inacessível", # Padrão caso falhe
        "Cargo Encontrado": False,
        "Modelo": "Não especificado",
        "Latam": False,
        "Obs": ""
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            resultado["Obs"] = f"Status Code: {response.status_code}"
            return resultado

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Limpeza
        for script in soup(["script", "style"]):
            script.extract()
        texto = soup.get_text().lower()
        cargo_alvo_lower = cargo_alvo.lower()

        # 1. Verifica Cargo
        if cargo_alvo_lower in texto:
            resultado["Cargo Encontrado"] = True
            resultado["Status"] = "✅ Vaga Detectada"
        else:
            resultado["Status"] = "❌ Vaga não encontrada"

        # 2. Verifica Modelo
        modelos_detectados = []
        if "remoto" in texto or "remote" in texto: modelos_detectados.append("Remoto")
        if "híbrido" in texto or "hybrid" in texto: modelos_detectados.append("Híbrido")
        if "presencial" in texto or "on-site" in texto: modelos_detectados.append("Presencial")
        
        if modelos_detectados:
            resultado["Modelo"] = ", ".join(modelos_detectados)

        # 3. Verifica LATAM
        termos_latam = ["latam", "latin america", "américa latina"]
        if any(t in texto for t in termos_latam):
            resultado["Latam"] = True

    except Exception as e:
        resultado["Obs"] = str(e)
    
    return resultado

# --- Interface do Aplicativo ---
st.set_page_config(page_title="Relatório de Vagas", layout="wide") # Layout mais largo para a tabela

st.title("📊 Relatório de Vagas em Lote")
st.markdown("Cole até **10 URLs** para gerar um relatório comparativo.")

# Entradas
col1, col2 = st.columns([1, 2])
with col1:
    cargo = st.text_input("Nome da Vaga (palavra-chave):", value="DevOps")
with col2:
    urls_input = st.text_area("Cole as URLs (uma por linha):", height=150, placeholder="https://site1.com/vaga\nhttps://site2.com/job")

if st.button("Gerar Relatório"):
    # Limpa e prepara a lista de URLs
    urls_lista = [u.strip() for u in urls_input.split('\n') if u.strip()]
    
    if not urls_lista:
        st.warning("Por favor, insira pelo menos uma URL.")
    else:
        # Limita a 10 para evitar sobrecarga (opcional, mas recomendado)
        if len(urls_lista) > 10:
            st.warning("Você inseriu mais de 10 URLs. Analisando apenas as 10 primeiras para garantir a performance.")
            urls_lista = urls_lista[:10]

        # Barra de progresso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        dados_relatorio = []

        # Loop de processamento
        for i, url in enumerate(urls_lista):
            status_text.text(f"Analisando site {i+1}/{len(urls_lista)}...")
            
            # Chama a função de análise
            dados = analisar_vaga(url, cargo)
            dados_relatorio.append(dados)
            
            # Atualiza barra
            progress_bar.progress((i + 1) / len(urls_lista))
            
            # Pequena pausa para ser educado com os servidores (evita bloqueio)
            time.sleep(0.5)

        status_text.text("Análise concluída!")
        progress_bar.empty()

        # --- Exibição dos Resultados ---
        st.divider()
        st.subheader(f"Relatório para: {cargo}")

        # Cria o DataFrame (Tabela)
        df = pd.DataFrame(dados_relatorio)

        # Reordena colunas para visualização melhor
        colunas_ordem = ["Status", "Cargo Encontrado", "Modelo", "Latam", "URL", "Obs"]
        df = df[colunas_ordem]

        # Mostra a tabela interativa
        st.dataframe(
            df, 
            column_config={
                "URL": st.column_config.LinkColumn("Link da Vaga"),
                "Latam": st.column_config.CheckboxColumn("É Latam?", default=False),
                "Cargo Encontrado": st.column_config.CheckboxColumn("Cargo Ok?", default=False),
            },
            hide_index=True,
            use_container_width=True
        )

        # Estatísticas rápidas
        total = len(df)
        encontrados = len(df[df["Cargo Encontrado"] == True])
        st.metric(label="Vagas que deram 'Match'", value=f"{encontrados} de {total}")
