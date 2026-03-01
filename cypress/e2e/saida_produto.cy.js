describe('Fluxo de Inventário - Saída de Itens', () => {
  it('Deve registrar uma retirada de produto com sucesso', () => {
    // 1. Acesso e Login
    cy.visit('http://localhost:8501')
    cy.get('input').eq(0).type('gustavo')
    cy.get('input').eq(1).type('123')
    cy.contains('Entrar').click({force: true})

    // 2. Abre o expander de Saída / Retirada
    cy.contains('Saída / Retirada').click({force: true})

   // 3. Seleção do Item (Produto)
    // Localizamos o input que pertence ao grupo "Item"
    cy.contains('label', 'Item')
      .parent()
      .find('input')
      .first()
      .type('TECLADO MECANICO{enter}', { force: true });

    // 4. Seleção do Destino
    cy.contains('label', 'Destino')
      .parent()
      .find('input')
      .first()
      .type('PRODUCAO{enter}', { force: true });

    // 5. Seleção do Responsável
    cy.contains('label', 'Responsável')
      .parent()
      .find('input')
      .first()
      .type('+ DIGITAR NOVO...{enter}', { force: true });
    
    // 6. Preenchimento do Nome (Novo Responsável)
    cy.contains('label', 'Nome')
      .parent()
      .find('input')
      .type('GUSTAVO VOLPI', { force: true });

    // 7. Quantidade de Saída (Limpando o padrão '1')
    cy.contains('label', 'Qtd Saída')
      .parent()
      .find('input')
      .clear({ force: true })
      .type('10', { force: true });

    // 8. Confirmação Final
    cy.contains('Confirmar Saída').click({ force: true });

    // 9. Validação de QA (Ajustada para o Rerun do Streamlit)
    // Reduzimos o tempo de espera e verificamos se o elemento EXISTIU 
    // antes do rerun, ou validamos a atualização do formulário.
    cy.contains('Saída registrada!', { timeout: 5000 }).should('exist');

    // Opcional: Validar que o formulário resetou (o campo de Nome fica vazio)
    cy.wait(2000); // Espera o rerun completar
    cy.contains('label', 'Nome').parent().find('input').should('have.value', '');
  })
})