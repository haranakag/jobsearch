import streamlit as st
import requests
from bs4 import BeautifulSoup

# --- Cole a função analisar_vaga aqui (mesma do passo anterior) ---
def analisar_vaga(url, cargo_alvo):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]): script.extract()
        texto = soup.get_text().lower()
        
        res = {"modelo": [], "latam": False, "cargo": False}
        
        # Buscas
        if cargo_alvo.lower() in texto: res["cargo"] = True
        
        if "remoto" in texto or "remote" in texto: res["modelo"].append("Remoto 🏠")
        if "híbrido" in texto or "hybrid" in texto: res["modelo"].append("Híbrido 🏢/🏠")
        if "presencial" in texto or "on-site" in texto: res["modelo"].append("Presencial 🏢")
        
        termos_latam = ["latam", "latin america", "américa latina"]
        if any(t in texto for t in termos_latam): res["latam"] = True
        
        return res
    except Exception as e:
        return {"erro": str(e)}
# ------------------------------------------------------------------

# Interface do Usuário
st.title("🕵️ Analisador de Vagas Automático")
st.markdown("Verifique se uma vaga atende aos seus requisitos de **Cargo**, **Modelo** e **Região**.")

# Entradas
url = st.text_input("Cole a URL da vaga:")
cargo = st.text_input("Qual cargo você procura?", value="DevOps Engineer")

if st.button("Analisar URL"):
    if url:
        with st.spinner('Lendo a página...'):
            dados = analisar_vaga(url, cargo)
        
        if "erro" in dados:
            st.error(f"Erro ao acessar o site: {dados['erro']}")
        else:
            st.success("Análise concluída!")
            
            # Exibição dos resultados em colunas
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("Cargo")
                if dados["cargo"]:
                    st.write(f"✅ Mencionado: **{cargo}**")
                else:
                    st.warning(f"❌ Não encontrei '{cargo}' exato")

            with col2:
                st.subheader("Modelo")
                if dados["modelo"]:
                    for m in dados["modelo"]:
                        st.write(f"✅ {m}")
                else:
                    st.warning("❓ Não especificado")

            with col3:
                st.subheader("Região")
                if dados["latam"]:
                    st.write("✅ **LATAM / América Latina**")
                else:
                    st.info("🌍 Não menciona LATAM explicitamente")
            
            # Expander para ver o texto bruto se necessário
            with st.expander("Ver detalhes técnicos"):
                st.json(dados)
    else:
        st.warning("Por favor, insira uma URL.")