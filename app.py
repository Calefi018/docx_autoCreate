import streamlit as st
from docx import Document
import google.generativeai as genai
import io
import json

# Puxa a chave de forma segura
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

# ---------------------------------------------------------
# FUNÇÃO DE IA COM O NOVO FILTRO ANTI-CHAVES
# ---------------------------------------------------------
def gerar_conteudo_ia(tema_curso, nome_modelo):
    """Gera o conteúdo usando o modelo dinâmico selecionado pelo usuário."""
    
    modelo = genai.GenerativeModel(nome_modelo)
    
    # PROMPT BLINDADO: Sem chaves nas variáveis para a IA não copiar o padrão
    prompt = f"""
    Atue como um estudante universitário do curso de {tema_curso}.
    Escreva as respostas para o Desafio Profissional focado no 'Caso Caroline' (Assistente que quer virar Analista, focando em Autorresponsabilidade, 10 Pilares da Vida, e Metas SMART).
    As respostas devem ser originais, sem plágio, mas seguindo a linha teórica de Paulo Vieira e Gestão de Carreiras.
    
    REGRA DE OURO: Retorne APENAS o texto limpo nas respostas. NUNCA use formatação Markdown (como **negrito** ou listas com *).
    
    Retorne APENAS um objeto JSON válido, contendo exatamente as chaves abaixo (SEM CHAVES DUPLAS). Não adicione markdown como ```json. Apenas as chaves e os textos.
    
    {{
        "ASPECTO_1": "texto curto do aspecto 1",
        "POR_QUE_1": "justificativa do aspecto 1",
        "ASPECTO_2": "texto curto do aspecto 2",
        "POR_QUE_2": "justificativa do aspecto 2",
        "ASPECTO_3": "texto curto do aspecto 3",
        "POR_QUE_3": "justificativa do aspecto 3",
        "CONCEITOS_TEORICOS": "Lista comentada de 4 conceitos teóricos com definição curta e como ajudam no caso.",
        "RESP_AUTORRESP": "Como a autorresponsabilidade explica o caso...",
        "RESP_PILARES": "Como os 10 pilares explicam o caso...",
        "RESP_SOLUCOES": "Que soluções o planejamento aponta...",
        "RESUMO_MEMORIAL": "Resumo do memorial analítico...",
        "CONTEXTO_MEMORIAL": "Contextualização do desafio...",
        "ANALISE_MEMORIAL": "Análise usando as teorias...",
        "PROPOSTAS_MEMORIAL": "Propostas de solução...",
        "CONCLUSAO_MEMORIAL": "Conclusão reflexiva...",
        "AUTOAVALIACAO_MEMORIAL": "Autoavaliação do processo de estudo..."
    }}
    """
    
    try:
        resposta = modelo.generate_content(prompt)
        texto_limpo = resposta.text.strip().replace("```json", "").replace("```", "")
        dicionario_dados = json.loads(texto_limpo)
        
        # --- NOVO FILTRO E RECONSTRUÇÃO DE VARIÁVEIS ---
        dicionario_higienizado = {}
        for chave, texto_gerado in dicionario_dados.items():
            
            # 1. Limpa o texto gerado (o valor) de qualquer sujeira e chaves duplas
            if isinstance(texto_gerado, str):
                texto_gerado = texto_gerado.replace("{{", "").replace("}}", "").replace("{", "").replace("}", "").replace("[", "").replace("]", "").replace("*", "").strip()
            else:
                texto_gerado = str(texto_gerado)
                
            # 2. Limpa a chave original do JSON
            chave_limpa = chave.replace("{", "").replace("}", "").strip()
            
            # 3. Monta o marcador garantindo que terá EXATAMENTE duas chaves.
            chave_marcador = f"{{{{{chave_limpa}}}}}"
            
            dicionario_higienizado[chave_marcador] = texto_gerado
            
        return dicionario_higienizado
        
    except Exception as e:
        st.error(f"Erro da IA ({nome_modelo}): {e}")
        return None

# ---------------------------------------------------------
# INTERFACE DO SITE (STREAMLIT)
# ---------------------------------------------------------
st.set_page_config(page_title="Gerador de Desafio Profissional", page_icon="📄")

st.title("Gerador de Trabalhos - Caso Caroline 📄")
st.write("Gere trabalhos originais mantendo a formatação do template.")

if "arquivo_pronto" not in st.session_state:
    st.session_state.arquivo_pronto = None
if "nome_arquivo" not in st.session_state:
    st.session_state.nome_arquivo = ""

modelos_disponiveis = []
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            modelos_disponiveis.append(m.name.replace('models/', ''))
except Exception as e:
    st.error("Erro ao conectar com a API do Google. Verifique sua chave.")

if modelos_disponiveis:
    modelo_escolhido = st.selectbox("Selecione o motor da IA (Recomendado: escolha os que terminam em 'flash'):", modelos_disponiveis)
    curso_alvo = st.text_input("Qual o curso? (Ex: Administração, Logística, Marketing)")

    if st.button("Gerar Documento Word", type="primary"):
        if curso_alvo:
            with st.spinner(f"Gerando trabalho com {modelo_escolhido}..."):
                
                dados_gerados = gerar_conteudo_ia(curso_alvo, modelo_escolhido)
                
                if dados_gerados:
                    arquivo_saida = io.BytesIO()
                    try:
                        preencher_template("TEMPLATE_COM_TAGS.docx", arquivo_saida, dados_gerados)
                        
                        st.session_state.arquivo_pronto = arquivo_saida.getvalue()
                        # Substitui espaços por underline para evitar problemas no nome do arquivo baixado
                        st.session_state.nome_arquivo = f"Desafio_Caroline_{curso_alvo.replace(' ', '_')}.docx"
                        
                        st.success("✅ Documento gerado e limpo com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao montar o Word: {e}")
        else:
            st.warning("⚠️ Digite o nome do curso.")
            
    if st.session_state.arquivo_pronto is not None:
        st.download_button(
            label="⬇️ Baixar Trabalho Pronto (.docx)",
            data=st.session_state.arquivo_pronto,
            file_name=st.session_state.nome_arquivo,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
else:
    st.error("Nenhum modelo compatível encontrado para esta chave API.")
