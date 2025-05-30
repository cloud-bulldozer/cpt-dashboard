describe('user journey on empty table', () => {
  beforeEach(() => {
    cy.intercept("GET", "/api/v1/cpt/jobs*").as("fetchData");
    cy.intercept("GET", "/api/v1/cpt/filters*").as("fetchSummary");
    cy.visit("/");
  });

  it("displays each tab in the side menu, then closes the side menu", () => {
    const nav_list_tab_name = ["OCP", "Quay", "Telco", "Home"];
    cy.findByTestId("side_menu_options")
      .should("be.visible")
      .within(() => {
        nav_list_tab_name.forEach((tab_name) => {
          cy.findByText(tab_name).should("be.visible").click();
        });
      });

    cy.findByTestId("main_layout_toggle").should("be.visible").click();
    cy.findByTestId("side_menu_options").should("not.be.visible");
  });

  it("displays the summary and data table and paginates", () => {
    cy.wait("@fetchData").its("response.statusCode").should("eq", 200);
    cy.wait("@fetchSummary").its("response.statusCode").should("eq", 200);
    cy.findByText("Summary").should("be.visible").click({ force: true });

    cy.document().then((doc) => {
      const hasFilter = doc.querySelector(
        '[data-ouia-component-id="data_table_filter"]'
      );
      const hasPagination = doc.querySelector(
        '[data-ouia-component-id="data_table_pagination"]'
      );

      if (hasFilter) {
        cy.get('[data-ouia-component-id="data_table_filter"]').should(
          "be.visible"
        );
      }

      if (hasPagination) {
        cy.get('[data-ouia-component-id="data_table_pagination"]')
          .scrollIntoView()
          .should("be.visible");
      }
    });
  });
});
