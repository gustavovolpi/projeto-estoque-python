@echo off
cd /d "C:\Users\gusta\projeto_estoque"
:: Ativa o ambiente virtual e roda o streamlit em modo 'headless' (sem abrir o navegador no servidor)
call venv\Scripts\activate
streamlit run app.py --server.headless true --server.port 8501
pause