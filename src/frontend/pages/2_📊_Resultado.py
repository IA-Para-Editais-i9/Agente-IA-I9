import streamlit as st


# ─────────────────────────────────────────────────────────────────────────────
# Acesso ao session_state
# ─────────────────────────────────────────────────────────────────────────────
def get_resultado():
    """Le o resultado da analise persistido pela tela de Upload (E1)."""
    return st.session_state.get("resultado_fit")


# ─────────────────────────────────────────────────────────────────────────────
# Empty state — quando o usuario acessa direto sem ter feito upload
# ─────────────────────────────────────────────────────────────────────────────
def render_empty_state():
    st.warning(
        "Nenhuma analise disponivel. Faca o upload de um edital "
        "na pagina **Upload** antes de visualizar o resultado."
    )
    if st.button("Ir para Upload", type="primary", use_container_width=True):
        st.switch_page("pages/1_📄_Upload.py")
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────
def render_header(resultado):
    titulo = resultado.get("edital_titulo", "Edital sem titulo")
    orgao = resultado.get("orgao", "Orgao nao informado")
    st.title("Diagnostico de Viabilidade")
    st.caption(f"{titulo} — {orgao}")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
def main():
    resultado = get_resultado()
    if not resultado:
        render_empty_state()
    render_header(resultado)


main()
