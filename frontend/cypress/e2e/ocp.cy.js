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

  it("expands a table row's details row to display cluster config metadata table", () => {
    const start_date = "2025-03-01"
    const end_date = "2025-03-30"

    // find date filter inputs
    cy.findByTestId("data_table_filter")      
      .find(`[ouiaid="date_filter"]`)
      .within(($date_filter) => {
        cy.wrap($date_filter)
          .find(`[class="react-date-picker__inputGroup"]`)
          .as("date_pickers_inputs");
      });
    
    // set start date
    // by convention, the first date input on the left receives the start date
    cy.get("@date_pickers_inputs")
      .first()
      .within(($date_pickers) => {
        cy.wrap($date_pickers)
          .get("input", {hidden: true})
          // the date value is saved within the hidden element
          // in this date picker group
          .get(":hidden")
          .type(start_date, {force: true});
      });

    // set end date
    // by convention, the next date input (last out of two) receives the end date
    cy.get("@date_pickers_inputs")
      .last()
      .within(($date_pickers) => {
        cy.wrap($date_pickers)
          .get("input", {hidden: true})
          // the date value is saved within the hidden element 
          // in this date picker group
          .get(":hidden")
          .type(end_date, {force: true});
      }); 
    
    cy.screenshot("main-data-table")

    // cy.findByTestId("main_data_table")
    //   .get("tbody")
    //   .find(`[data-ouia-component-type="PF5/TableRow"]`, 
    //       {hidden: false})
    //   .as("table_row")
    //   .first();

    // // in the list of table row elements, each table row is 
    // // paired with a subsequent hidden row that can be expanded
    // // to display details
    // cy.get("@table_row")
    //   .next()
    //   .as("expandable_rows")        
    //   .should("not.be.visible");

    // cy.get("@table_row")
    //   .find(`[data-ouia-component-type="PF5/Button"]`, 
    //       {expanded: false})
    //   .first()
    //   .as("tgl_details")
    //   .click();

    // cy.get("@expandable_rows")
    //   .first()
    //   .should("be.visible");

    // // cluster config input
    // cy.get("@expandable_rows")
    //   .first()
    //   .find(`[data-ouia-component-id="metadata-table"]`)
    //   .should("be.visible");

    // // close expandable row
    // cy.get("@tgl_details")
    //   .click();
    // cy.get("@expandable_rows")
    //   .should("not.be.visible");
  });
});
