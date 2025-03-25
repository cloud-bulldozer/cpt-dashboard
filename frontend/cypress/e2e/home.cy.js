describe('basic user journey', () => {
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

  // it.only("scrolls to bottom and paginates", () => {
  //   cy.findByTestId("side_menu_options")
  //     .should("be.visible")
  //     .within(() => {
  //       cy.findByText("OCP")
  //         .should("be.visible")
  //         .click();
  //     });
  //   cy.findByTestId("main_layout_toggle")  
  //     .click();
  //   cy.findByTestId("side_menu_options")
  //     .should("not.be.visible");

  //   cy.findByTestId("data_table_pagination")
  //     .scrollIntoView()
  //     .should("be.visible")
  //     // .within(() => {
  //     //   cy.find(['data-action="next"'])
  //     //     .click();
  //     // })
  //     // .find(['data-action="next"'])
  //     // .click();
  // });

  it.only("explores OCP data table", () => {
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

    // cy.findByTestId("main_data_table")
    //   .within(($table) => {
    //     cy.wrap($table);
    //     // $table.get("tbody button")
    //     // cy.wrap($button)
    //     $table.findByTestId("OUIA-Generated-TableRow-2")
    //     // $table.findByRole("rowgroup")
    //       // .first()
    //       // .should("not.be.expanded")
    //       // .within()
    //       // .click();
    //   });
      // .get("tbody button")
      // .within(() => {
      //   cy.findByRole("rowgroup")
      // })
      // .get("tbody button").first($button => {
      //   cy.wrap($button).click();
      // })
      // .get("tbody button")
      // .wrap($button)
      // .click();

      // cy.findByTestId("OUIA-Generated-TableRow-2")
      //   .within(($tr) => {
      //     $tr.findByRole("button")
      //       .click();
      //   })
      cy.findByTestId("main_data_table")
        .get("tbody")
        .find(`[data-ouia-component-type="PF5/TableRow"]`)
        .as("tr")
        .first();

        // .find(`[data-ouia-component-type="PF5/Button"]`, {expanded: false})
        // .as("tgl_details")
        // .click();

      cy.get("@tr")
        .next()
        .as("expandable_row");        
      cy.get("@expandable_row")
        .should("not.be.visible");

      cy.get("@tr")
        .find(`[data-ouia-component-type="PF5/Button"]`, {expanded: false})
        .first()
        // .as("tgl_details")
        .click();

      cy.get("@expandable_row")
        .should("be.visible");        
      // cy.get("@tr")
      //   .next()
      //   .as("expandable_rw")
      //   .should("be.visible")
      // cy.get("@tgl_details")
        // .should("be.expanded");
        // .should("have.class", "active");

        // .click();
      
      
  });
});
