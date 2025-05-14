describe('user journey on empty table', () => {
  beforeEach(() => {
    cy.visit("/");
  });

  it("displays each tab in the side menu, then closes the side menu", () => {
    const nav_list_tab_name = ["OCP", "Quay", "Telco", "Home"];
    cy.findByTestId("side_menu_options")
      .should("be.visible")
      .within(() => {
        nav_list_tab_name.forEach((tab_name) => {
          cy.findByText(tab_name)
            .should("be.visible")
            .click();
      })
    });

    cy.findByTestId("main_layout_toggle")
      .should("be.visible")
      .click();
    cy.findByTestId("side_menu_options")
      .should("not.be.visible");
  });

  it("displays data table filter", () => {    
    cy.findByTestId("data_table_filter")
      .should("be.visible");
  });
});
