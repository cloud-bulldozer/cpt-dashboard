describe('template spec', () => {
  const url_gui = "http://localhost:3000";
  it('passes', () => {
    cy.visit(url_gui)
    const nav_list_tab_name = ["OCP", "Quay", "Telco", "Home"];
    cy.findByTestId("nav_list").each(($el) => {
      nav_list_tab_name.forEach((tab_name) => {
        cy.wrap($el).findByText(tab_name).should("exist").click();
      })
    });

    // close sidebar masthead with hamburger toggle
    cy.get('[data-ouia-component-id="main_layout_toggle"]').should("exist").click();
    
    // cannot click summary b/c it requires a real user event
    // b/c its parent css has pointer-events: none
    cy.findAllByText("Summary").should("exist");
    // cy.get('[data-ouia-component-id="summary_toggle"]', {withinSubject:null}).click();
    // cy.get('[ouiaid="summary_toggle"]').click();
    
    
    // add scroll into view
    // add table exists
    // add paginate
  });
});