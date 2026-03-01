describe('Fluxo de Inventário - Cadastro de Itens', () => {
  it('Deve cadastrar um novo produto com sucesso', () => {
    // 1. Acesso e Login (Sempre garantindo que o localhost:8501 está rodando!)
    cy.visit('http://localhost:8501')
    cy.get('input').eq(0).type('gustavo')
    cy.get('input').eq(1).type('123')
    cy.contains('Entrar').click({force: true})

    // 2. Abre o expander de Entrada
    cy.contains('Entrada de Estoque').click({force: true})

    // 3. Preenchimento do Novo Produto
    // Deixamos o dropdown original em "Choose an option"
    cy.get('input').eq(3).type('Teclado Mecânico', { force: true }) 

    // Seleção do Tipo (Dropdown)
    cy.get('input').eq(4).click({ force: true })
    cy.contains('Por unidade').click({ force: true })

    // Quantidade - Usando clear() para garantir o campo limpo
    cy.get('input').eq(5).clear({ force: true }).type('10', { force: true })

    // 4. Ação de Confirmar
    cy.contains('Confirmar Entrada').click({ force: true })
    
    // 5. Sincronização
    cy.wait(2000)

    // O 'i' no final do regex torna a busca Insensitive (ignora maiúsculas/minúsculas)
    // E removemos o 'ê' da busca para bater com o seu banco normalizado
    cy.contains(/TECLADO MECANICO/i, { timeout: 15000 }).should('exist')
  })
})