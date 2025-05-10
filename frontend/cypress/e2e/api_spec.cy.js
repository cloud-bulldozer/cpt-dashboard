describe('API Connectivity Check', () => {
  it.only('Checks backend API through frontend proxy', () => {
    cy.request({
      url: '/api/v1/ocp/jobs',  // explicitly relative to baseUrl
      failOnStatusCode: false,    // ensures Cypress doesn't immediately fail
    }).then((response) => {
      cy.log('Status:', response.status);
      cy.log('Headers:', JSON.stringify(response.headers));
      cy.log('Body:', JSON.stringify(response.body));
      
      // Expect a successful response for diagnosis
      expect(response.status).to.eq(200);
    });
  });
});
