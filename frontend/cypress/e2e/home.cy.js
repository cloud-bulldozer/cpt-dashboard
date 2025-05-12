// Cypress.on('window:before:load', (win) => {
//   win.onerror = (msg, src, line, col, err) => {
//     Cypress.task('log', `✖ Uncaught Error: ${msg} at ${src}:${line}:${col}`)
//   }
//   const origError = win.console.error.bind(win.console)
//   win.console.error = (...args) => {
//     Cypress.task('log', `✖ console.error: ${args.join(' ')}`)
//     origError(...args)
//   }
// });

describe.only('basic user journey', () => {
  beforeEach(() => {
    // cy.intercept("GET", "/api/v1/cpt/jobs*").as("getJobs");
    cy.visit("/");
    // cy.wait("@getJobs");

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

    // cy.get('body')
    //   .invoke('html')
    //   .then(fullHtml => {
    //     cy.task("log", `HEADLESS PAGE HTML:\n${fullHtml}`)
    //   });      
  });

  it("displays the summary and data table and paginates", () => {    
    // cy.findByTestId("data_table_filter")
    //   .should("be.visible");

    // cy.findByTestId("data_table_pagination")
    //   .scrollIntoView()
    //   .should("be.visible");
  });
});
