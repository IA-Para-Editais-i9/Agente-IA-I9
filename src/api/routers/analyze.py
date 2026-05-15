"""
Squad Responsável: Squad D — Orquestração & Backend

Responsabilidades (Task D3):
- Criar endpoint `POST /analisar-edital`
- Receber upload de PDF de edital (validação: só PDF, máx 100MB)
- Acionar o pipeline completo (PyMuPDF + Tesseract → ChromaDB → Agente 1 → Agente 2)
- Retornar o JSON final com o `ResultadoFit`
"""
