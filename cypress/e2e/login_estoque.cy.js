describe('Testes de Interface - Controle de Estoque', () => {
  it('Deve realizar login com sucesso e entrar no sistema', () => {
    cy.visit('http://localhost:8501')

    // 1. Preenche os campos
    cy.get('input').eq(0).type('GUSTAVO')
    cy.get('input').eq(1).type('123')

    // 2. Tenta clicar especificamente no botão
    // O {force: true} ajuda se houver algo "na frente" do botão
    cy.get('button').contains('Login').click({force: true})

    // Procura por qualquer elemento que contenha "Login" e clica nele
    cy.contains('Login').click({force: true})
  })
})