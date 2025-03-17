describe('basic user journey', () => {
  beforeEach(() => {
    cy.visit("/");
  });
  
  it("displays each tab in the side menu, then closes the side menu", () => {
    cy.findByTestId("main_layout_toggle")
      .should("be.visible");
    cy.findByTestId("side_menu")
      .should("be.visible");      

    const nav_list_tab_name = ["OCP", "Quay", "Telco", "Home"];
    cy.findByTestId("side_menu")
      .within(() => {
        nav_list_tab_name.forEach((tab_name) => {
          cy.findByText(tab_name)
            .should("be.visible")
            .click();
      })
    });

    cy.findByTestId("main_layout_toggle")
      .click();
    cy.findByTestId("side_menu")
      .should("not.be.visible");
  });

  it("displays the summary and data table and paginates", () => {
    cy.findByText('Summary')
      .should('be.visible') 
      .click({force: true});
    
    cy.findByTestId("data_table_filter")
      .should("be.visible");

    cy.findByTestId("data_table_pagination")
      .scrollIntoView()
      .should("be.visible");
  });
});