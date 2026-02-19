import streamlit as st
from docx import Document
import google.generativeai as genai
import io

# Configuração da API do Gemini (Você precisará gerar uma chave gratuita no Google AI Studio)
CHAVE_API = "COLOQUE_SUA_CHAVE_API_AQUI"
genai.configure(api_key=CHAVE_API)

# ---------------------------------------------------------
# MANTENDO A ESTRUTURA ORIGINAL DO CÓDIGO INTACTA
# ---------------------------------------------------------
def preencher_template(caminho_template, caminho_saida, dicionario_dados):
    """
    Lê um template Word, substitui os marcadores e salva um novo arquivo
    sem alterar a estrutura original.
    """
    doc = Document(caminho_template)

    for paragrafo in doc.paragraphs:
        for marcador, texto_novo in dicionario_dados.items():
            if marcador in paragrafo.text:
                paragrafo.text = paragrafo.text.replace(marcador, texto_novo)

    for tabela in doc.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                for paragrafo in celula.paragraphs:
                    for marcador, texto_novo in dicionario_dados.items():
                        if marcador in paragrafo.text:
                            paragrafo.text = paragrafo.text.replace(marcador, texto_novo)

    doc.save(caminho_saida)
# ---------------------------------------------------------

def gerar_conteudo_ia(tema_curso):
    """Função para pedir ao Gemini as respostas exclusivas baseadas no curso."""
    modelo = genai.GenerativeModel("gemini-1.5-pro")
    
    prompt = f"""
    Crie respostas para o Desafio Profissional (Caso Caroline) focado no curso de {tema_curso}.
    Retorne APENAS um dicionário Python válido com as chaves e os textos, sem formatação markdown extra, assim:
    {{
        "{{ASPECTO_1}}": "texto aqui",
        "{{POR_QUE_1}}": "texto aqui",
        "{{RESUMO_MEMORIAL}}": "texto aqui"
    }}
    """
    resposta = modelo.generate_content(prompt)
    try:
        # Converte a string retornada pela IA em um dicionário real
        return eval(resposta.text)
    except:
        st.error("Erro ao gerar o conteúdo com a IA. Tente novamente.")
        return None

# --- INTERFACE DO SITE (STREAMLIT) ---
st.title("Gerador Automático de Trabalhos Acadêmicos 📄")
st.write("Gere versões únicas do Desafio Profissional mantendo a formatação do template.")

# Campo para o usuário digitar para qual curso é o trabalho
curso_alvo = st.text_input("Qual o curso/foco deste trabalho? (Ex: Administração, Logística, RH)")

if st.button("Gerar Trabalho"):
    if curso_alvo:
        with st.spinner("A IA está escrevendo o trabalho e montando o Word..."):
            
            # 1. Pede para a IA gerar os textos únicos
            dados_gerados = gerar_conteudo_ia(curso_alvo)
            
            if dados_gerados:
                # 2. Prepara um arquivo em memória (para poder baixar no site)
                arquivo_saida = io.BytesIO()
                
                # 3. Executa a nossa função original
                preencher_template("TEMPLATE_COM_TAGS.docx", arquivo_saida, dados_gerados)
                
                # 4. Libera o botão de download
                st.success("Trabalho gerado com sucesso!")
                st.download_button(
                    label="⬇️ Baixar Documento Word (.docx)",
                    data=arquivo_saida.getvalue(),
                    file_name=f"Desafio_Caroline_{curso_alvo}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
    else:
        st.warning("Por favor, digite o nome do curso.")
