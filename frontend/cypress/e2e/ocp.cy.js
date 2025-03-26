describe('ocp user journey', () => {
  beforeEach(() => {
    cy.visit("/ocp");
    cy.findByTestId("side_menu_options")
      .should("be.visible")
      .within(() => {
        cy.findByText("OCP")
          .should("be.visible")
          .click();
      });
    cy.findByTestId("main_layout_toggle")  
      .click();
    cy.findByTestId("side_menu_options")
      .should("not.be.visible");
  });

  it.only("expands a table row's details row to cluser config and benchmark results", () => {
    cy.findByTestId("main_data_table")
      .get("tbody")
      .find(`[data-ouia-component-type="PF5/TableRow"]`, 
          {hidden: false})
      .as("table_row")
      .first();

    // each table row is paired with a subsequent hidden row
    // that can be expanded to display details
    cy.get("@table_row")
      .next()
      .as("expandable_row")        
      .should("not.be.visible");

    cy.get("@table_row")
      .find(`[data-ouia-component-type="PF5/Button"]`, 
          {expanded: false})
      .first()
      .click();

    cy.get("@expandable_row")
      .should("be.visible");        

  });
});
