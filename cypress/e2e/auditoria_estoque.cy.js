describe('Fluxo de Auditoria - Rastreabilidade de Movimentações', () => {
  it('Deve filtrar e validar a última saída do Teclado Mecânico', () => {
    // 1. Login
    cy.visit('http://localhost:8501')
    cy.get('input').eq(0).type('gustavo')
    cy.get('input').eq(1).type('123')
    cy.contains('Entrar').click({force: true})

    // 2. Navegação para Auditoria
    // Clicamos no rádio button da sidebar
    cy.contains('Auditoria').click({force: true})
    cy.contains('Histórico de Movimentações').should('be.visible')

    // 3. Aplicação de Filtros
    // Filtro de Produto
    cy.contains('label', 'Produto').parent().find('input').first()
      .type('TECLADO MECANICO{enter}', { force: true })

    // Filtro de Tipo de Movimentação (Onde estava falhando)
    // Localizamos o label exato para não confundir com outros dropdowns
    cy.contains('label', 'Tipo de Movimentação').parent().find('input').first()
      .type('SAÍDA{enter}', { force: true })

    // Filtro de Operador
    cy.contains('label', 'Operador do Sistema').parent().find('input').first()
      .type('gustavo{enter}', { force: true })

    // Filtro de Operador do Sistema
    cy.contains('label', 'Operador do Sistema').parent().find('input').first()
      .type('gustavo{enter}', { force: true })

    // Filtro de Colaborador/Responsável
    cy.contains('label', 'Colaborador/Responsável').parent().find('input').first()
      .type('GUSTAVO VOLPI{enter}', { force: true })

    // 4. Validação dos Resultados na Tabela
    // Verificamos se a linha com a saída de 10 unidades aparece
    cy.get('div').contains('SAÍDA').should('exist')
    cy.get('div').contains('10 un').should('exist')
    cy.get('div').contains('PRODUCAO').should('exist')

    // 5. Verificação de Integridade (Excel)
    // Garante que o botão de exportação está disponível para o admin
    cy.contains('Exportar Relatório para Excel').should('be.visible')
  })
})