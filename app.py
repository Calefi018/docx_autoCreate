import streamlit as st
from docx import Document
import google.generativeai as genai
import io
import json

# Segurança: A chave é puxada do painel do Streamlit, não fica exposta no código.
CHAVE_API = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=CHAVE_API)

# ---------------------------------------------------------
# FUNÇÃO DE PREENCHIMENTO (ESTRUTURA MANTIDA INTACTA)
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
    """Solicita à IA que gere o conteúdo único em formato JSON compatível com as tags."""
    modelo = genai.GenerativeModel("gemini-pro")
    
    # Prompt detalhado para garantir que a IA devolva as respostas certas sem plágio
    prompt = f"""
    Atue como um estudante universitário do curso de {tema_curso}.
    Escreva as respostas para o Desafio Profissional focado no 'Caso Caroline' (Assistente que quer virar Analista, focando em Autorresponsabilidade, 10 Pilares da Vida, e Metas SMART).
    As respostas devem ser originais, sem plágio, mas seguindo a linha teórica de Paulo Vieira e Gestão de Carreiras.
    
    Retorne APENAS um objeto JSON válido, contendo exatamente as chaves abaixo com seus respectivos textos gerados. Não adicione markdown como ```json. Apenas as chaves e os textos.
    
    {{
        "{{ASPECTO_1}}": "texto curto do aspecto 1",
        "{{POR_QUE_1}}": "justificativa do aspecto 1",
        "{{ASPECTO_2}}": "texto curto do aspecto 2",
        "{{POR_QUE_2}}": "justificativa do aspecto 2",
        "{{ASPECTO_3}}": "texto curto do aspecto 3",
        "{{POR_QUE_3}}": "justificativa do aspecto 3",
        "{{RESP_AUTORRESP}}": "Como a autorresponsabilidade explica o caso...",
        "{{RESP_PILARES}}": "Como os 10 pilares explicam o caso...",
        "{{RESP_SOLUCOES}}": "Que soluções o planejamento aponta...",
        "{{RESUMO_MEMORIAL}}": "Resumo do memorial analítico...",
        "{{CONTEXTO_MEMORIAL}}": "Contextualização do desafio...",
        "{{ANALISE_MEMORIAL}}": "Análise usando as teorias...",
        "{{PROPOSTAS_MEMORIAL}}": "Propostas de solução...",
        "{{CONCLUSAO_MEMORIAL}}": "Conclusão reflexiva...",
        "{{AUTOAVALIACAO_MEMORIAL}}": "Autoavaliação do processo de estudo..."
    }}
    """
    
    try:
        resposta = modelo.generate_content(prompt)
        texto_limpo = resposta.text.strip().replace("```json", "").replace("```", "")
        dicionario_dados = json.loads(texto_limpo)
        return dicionario_dados
    except Exception as e:
        st.error(f"Erro ao gerar ou formatar o conteúdo com a IA. Detalhes: {e}")
        return None

# ---------------------------------------------------------
# INTERFACE DO SITE (STREAMLIT)
# ---------------------------------------------------------
st.set_page_config(page_title="Gerador de Desafio Profissional", page_icon="📄")

st.title("Gerador de Trabalhos - Caso Caroline 📄")
st.write("Insira o curso alvo para gerar um trabalho totalmente original e sem plágio, mantendo a formatação padrão da faculdade.")

curso_alvo = st.text_input("Qual o curso? (Ex: Administração, Logística, Marketing)")

if st.button("Gerar Documento Word", type="primary"):
    if curso_alvo:
        with st.spinner("Conectando à IA e redigindo o trabalho... (Isso pode levar alguns segundos)"):
            
            # Gera os dados únicos com a IA
            dados_gerados = gerar_conteudo_ia(curso_alvo)
            
            if dados_gerados:
                # Cria um arquivo em memória para download direto no navegador
                arquivo_saida = io.BytesIO()
                
                try:
                    # Aplica as variáveis no template do Word
                    preencher_template("TEMPLATE_COM_TAGS.docx", arquivo_saida, dados_gerados)
                    
                    st.success("✅ Documento gerado com sucesso!")
                    
                    # Disponibiliza o download do arquivo preenchido
                    st.download_button(
                        label="⬇️ Baixar Trabalho Pronto (.docx)",
                        data=arquivo_saida.getvalue(),
                        file_name=f"Desafio_Caroline_{curso_alvo}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                except Exception as e:
                    st.error(f"Erro ao processar o arquivo Word. Verifique se o TEMPLATE_COM_TAGS.docx está no GitHub. Erro: {e}")
    else:
        st.warning("⚠️ Por favor, digite o nome do curso antes de gerar.")
