describe('Testes de Interface - Controle de Estoque', () => {
  it('Deve realizar login com sucesso e entrar no sistema', () => {
    cy.visit('http://localhost:8501')

    // 1. Preenche os campos normalmente
    cy.get('input').eq(0).type('gustavo')
    cy.get('input').eq(1).type('123')

    // 2. CORREÇÃO: Altere de 'Login' para 'Entrar'
    // O {force: true} ajuda se o Streamlit tiver camadas sobre o botão
    cy.contains('Entrar').click({force: true})

    // 3. Aguarda o sistema carregar a próxima tela
    cy.contains('Estoque', { timeout: 10000 }).should('be.visible')
  })
})