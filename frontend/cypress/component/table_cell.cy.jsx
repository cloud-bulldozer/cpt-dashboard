import TableCell from "@/components/atoms/TableCell";
import { formatDateTime, uid } from "@/utils/helper.js";

describe("table cell", () => {
  it("displays successful job status", () => {
    const item = {"jobStatus": "success"};
    const col = {"value": "jobStatus", name: "status"};
    cy.mount(<TableCell item={item} col={col} />);     

    cy.findByText("Success")
      .should("be.visible");
    cy.findByTestId("check_circle_icon")
      .should("be.visible");
  });

  it("displays failed job status", () => {
    const item = {"jobStatus": "failed"};
    const col = {"value": "jobStatus", name: "status"};
    cy.mount(<TableCell item={item} col={col} />);     

    cy.findByText("Failure")
      .should("be.visible");
    cy.findByTestId("exclamation_circle_icon")
      .should("be.visible");
  });

  it("displays and links a build url", () => {
    const buildUrlExp = "my.build.url";
    const item = {buildUrl: buildUrlExp};
    const col = {"value": "buildUrl", name: "build"};
    cy.mount(<TableCell item={item} col={col} />);      

    cy.findByText("Job")
      .should("be.visible");
    
    // assert clicking the build url creates
    // an http request to the given build url
    cy.intercept(buildUrlExp, (req) => {
      cy.findByTestId("external_link_square_icon")
        .should("be.visible")
        .click();
      expect(req.url).to.be(buildUrlExp);
    });
  });

  it("displays a start date", () => {
    const test_date = "1000-01-30";
    const item = {startDate: test_date};
    const col = {value: "startDate", name: "startDate"};
    cy.mount(<TableCell item={item} col={col} />);

    cy.findByText(formatDateTime(test_date))
      .should("be.visible");
  });

  it("displays an end date", () => {
    const test_date = "1000-01-30";
    const item = {endDate: test_date};
    const col = {value: "endDate", name: "endDate"};
    cy.mount(<TableCell item={item} col={col} />);

    cy.findByText(formatDateTime(test_date))
      .should("be.visible");
  });

  it("displays some text", () => {
    const cell_text = "r7j5";
    const item = {"robot": cell_text};
    const col = {"value": "robot", name: "robot"};
    cy.mount(<TableCell item={item} col={col} />);
    
    cy.findByText(cell_text)
      .should("be.visible");
  })
});