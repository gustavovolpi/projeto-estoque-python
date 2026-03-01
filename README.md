# 📦 Controle de Estoque - Python

Sistema desenvolvido em **Python** utilizando a biblioteca **Streamlit** para interface e **SQLite** para persistência de dados. O projeto foi estruturado para gerenciar entradas e saídas de estoque por setores, com foco em auditoria e rastreabilidade.

## 🚀 Funcionalidades Principais

- **📦 Gestão de Estoque:** Entradas por unidade ou embalagem (caixa, pacote, etc.) e saídas com registro de colaborador responsável.
- **📜 Auditoria Completa:** Histórico detalhado de movimentações com filtros por data, setor, operador e produto.
- **🛡️ Painel Administrativo:** Controle de acesso (Login), gerenciamento de tipos de embalagens, soft delete de produtos e logs de ajustes.
- **📊 Exportação de Dados:** Geração de relatórios em Excel (.xlsx) tanto para o saldo atual quanto para o histórico de auditoria.
- **⚡ Automação:** Scripts (.bat) inclusos para inicialização rápida e rotinas de backup do banco de dados.

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.10+
- **Interface:** Streamlit
- **Banco de Dados:** SQLite
- **Manipulação de Dados:** Pandas
- **Versionamento:** Git

## 📂 Estrutura de Pastas

```text
PROJETO_ESTOQUE/
├── scripts/            # Scripts de automação (.bat e .vbs)
│   ├── iniciar_estoque.bat
│   └── backup_estoque.bat
├── utils/              # Scripts de utilidade (setup, reset de senha)
│   ├── setup_estoque.py
│   └── criar_usuario.py
├── app.py              # Arquivo principal do sistema
├── .gitignore          # Configurações de versionamento
└── requirements.txt    # Dependências do projeto

⚙️ Como Executar o Projeto
Clonar o repositório:

# Clonar o repositório:
git clone https://github.com/gustavovolpi/projeto-estoque.git
cd projeto-estoque

python -m venv venv
# Windows:
.\venv\Scripts\activate
Instalar as dependências:

pip install -r requirements.txt
Inicializar o Banco de Dados:
Execute o script de setup para criar as tabelas necessárias e o usuário administrador padrão.

python utils/setup_estoque.py
Rodar a aplicação:

streamlit run app.py

Foco em Qualidade (QA)
Rastreabilidade: Cada ação no sistema gera um rastro (Causa e Efeito) no banco de dados.

Validação de Inputs: Normalização de textos e prevenção de saldos negativos.

Tratamento de Erros: Migrações automáticas de colunas e tratamento de exceções em consultas SQL

Desenvolvido por Gustavo Volpi — https://www.linkedin.com/in/gustavo-volpi/