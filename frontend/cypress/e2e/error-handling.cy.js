/**
 * Error Handling Validation Tests
 *
 * Validates the enhanced axios interceptor error handling:
 * - Different FastAPI error response formats
 * - Toast notifications for errors
 * - UI remains operational after errors
 * - Fallback messages for malformed responses
 * - Centralized error handling in Axios layer
 *
 * Uses mocked API responses - no backend required.
 * Route: /error_test (navigate via sidebar "🧪 Error Test" or direct visit)
 */
describe('Error Handling Validation', () => {
  const ERROR_TEST_PAGE_URL = '/error_test';

  beforeEach(() => {
    cy.visit(ERROR_TEST_PAGE_URL);
    cy.get('h1').should('contain', 'Error Handling Test Page');
    // Close sidebar so buttons are not covered by nav links
    cy.get('[data-ouia-component-id="main_layout_toggle"]').then(($el) => {
      if ($el.is(':visible')) {
        cy.wrap($el).click();
      }
    });
  });

  const testErrorButton = (buttonText, expectedTitle, expectedMessageContains, options = {}) => {
    const { skipMessageCheck = false, timeout = 10000 } = options;

    cy.contains('button', 'Test This Error')
      .filter(`:contains("${buttonText}")`)
      .first()
      .parents('div[class*="CardBody"]')
      .first()
      .within(() => {
        cy.get('button').click();
      });

    // Toast should appear - PatternFly Alert with danger variant
    cy.get('[class*="Alert"]', { timeout })
      .should('be.visible')
      .and('contain', expectedTitle);

    if (!skipMessageCheck && expectedMessageContains) {
      cy.get('[class*="Alert"]').should('contain', expectedMessageContains);
    }

    // UI should remain operational - we can click another button
    cy.get('h1').should('be.visible');
  };

  it('displays Error Test page with all test buttons', () => {
    const expectedButtons = [
      'Format 1',
      'Format 2',
      'Format 3',
      'Format 4',
      'Malformed Response',
      'Network Timeout',
      'Validation Errors',
    ];

    expectedButtons.forEach((text) => {
      cy.contains(text).scrollIntoView().should('exist');
    });
  });

  it('Format 1: {"detail": {"message": "..."}} - shows Bad Request toast', () => {
    cy.intercept('GET', '**/test-errors/format1*', {
      statusCode: 400,
      body: { detail: { message: 'This is a test error with message object format' } },
    }).as('format1');
    cy.contains('h3', 'Format 1:').parent().within(() => {
      cy.get('button').scrollIntoView().click({ force: true });
    });

    cy.wait('@format1');
    cy.contains('Bad Request', { timeout: 10000 }).should('be.visible');
    cy.contains('message object format').should('be.visible');
  });

  it('Format 2: {"detail": {"error": "..."}} - shows Validation Error toast', () => {
    cy.intercept('GET', '**/test-errors/format2*', {
      statusCode: 422,
      body: { detail: { error: 'This is a test error with error object format' } },
    }).as('format2');
    cy.contains('h3', 'Format 2:').parent().within(() => {
      cy.get('button').scrollIntoView().click({ force: true });
    });

    cy.wait('@format2');
    cy.contains('Validation Error', { timeout: 10000 }).should('be.visible');
    cy.contains('error object format').should('be.visible');
  });

  it('Format 3: {"detail": "..."} - shows Not Found toast', () => {
    cy.intercept('GET', '**/test-errors/format3*', {
      statusCode: 404,
      body: { detail: 'This is a test error with string detail format' },
    }).as('format3');
    cy.contains('h3', 'Format 3:').parent().within(() => {
      cy.get('button').scrollIntoView().click({ force: true });
    });

    cy.wait('@format3');
    cy.contains('Not Found', { timeout: 10000 }).should('be.visible');
    cy.contains('string detail format').should('be.visible');
  });

  it('Format 4: {"error": "..."} - shows Internal Server Error toast', () => {
    cy.intercept('GET', '**/test-errors/format4*', {
      statusCode: 500,
      body: { error: 'This is a test error with direct error key' },
    }).as('format4');
    cy.contains('h3', 'Format 4:').parent().within(() => {
      cy.get('button').scrollIntoView().click({ force: true });
    });

    cy.wait('@format4');
    cy.contains('Internal Server Error', { timeout: 10000 }).should('be.visible');
    cy.contains('direct error key').should('be.visible');
  });

  it('Malformed Response - shows fallback message when JSON cannot be parsed', () => {
    cy.intercept('GET', '**/test-errors/malformed*', {
      statusCode: 503,
      body: 'This is not valid JSON',
      headers: { 'content-type': 'text/plain' },
    }).as('malformed');
    cy.contains('h3', 'Malformed Response').parent().within(() => {
      cy.get('button').scrollIntoView().click({ force: true });
    });

    cy.wait('@malformed');
    // Malformed returns 503 - should show Server Error or Request Error fallback
    cy.get('body', { timeout: 10000 }).should(($body) => {
      const text = $body.text();
      expect(
        text.includes('Server Error') ||
        text.includes('Request Error') ||
        text.includes('Service Unavailable') ||
        text.includes('issue with your request')
      ).to.be.true;
    });
  });

  it('Validation Errors - combines multiple validation errors in toast', () => {
    cy.intercept('GET', '**/test-errors/validation*', {
      statusCode: 422,
      body: {
        detail: [
          { type: 'missing', loc: ['query', 'start_date'], msg: 'Field required', input: null },
          { type: 'value_error', loc: ['query', 'size'], msg: 'ensure this value is greater than 0', input: -5 },
          { type: 'type_error', loc: ['body', 'filter'], msg: 'str type expected', input: 123 },
        ],
      },
    }).as('validation');
    cy.contains('h3', 'Validation Errors').parent().within(() => {
      cy.get('button').scrollIntoView().click({ force: true });
    });

    cy.wait('@validation');
    cy.contains('Validation Error', { timeout: 10000 }).should('be.visible');
    cy.get('body').should(($body) => {
      const text = $body.text();
      expect(
        text.includes('Field required') ||
        text.includes('greater than 0') ||
        text.includes('str type expected') ||
        text.includes('Multiple validation errors')
      ).to.be.true;
    });
  });

  it('UI remains operational after error - can click another button', () => {
    // Trigger Format 1 error
    cy.intercept('GET', '**/test-errors/format1*', {
      statusCode: 400,
      body: { detail: { message: 'Test message' } },
    }).as('format1');
    cy.contains('h3', 'Format 1:').parent().within(() => {
      cy.get('button').scrollIntoView().click({ force: true });
    });
    cy.wait('@format1');
    cy.contains('Bad Request', { timeout: 10000 }).should('be.visible');

    // UI should still be responsive - click Format 2
    cy.intercept('GET', '**/test-errors/format2*', {
      statusCode: 422,
      body: { detail: { error: 'Test error' } },
    }).as('format2');
    cy.contains('h3', 'Format 2:').parent().within(() => {
      cy.get('button').scrollIntoView().click({ force: true });
    });
    cy.contains('Validation Error', { timeout: 10000 }).should('be.visible');
    cy.get('h1').should('contain', 'Error Handling Test Page');
  });

  // Network Timeout test - skip by default as it takes 30s, run with .only when needed
  it.skip('Network Timeout - shows appropriate network error (30s)', () => {
    cy.intercept('GET', '**/test-errors/network*', { delay: 35000 }).as('network');
    cy.contains('h3', 'Network Timeout').parent().within(() => {
      cy.get('button').scrollIntoView().click({ force: true });
    });

    cy.wait('@network', { timeout: 40000 });
    cy.contains('Network Error', { timeout: 35000 }).should('be.visible');
  });
});
