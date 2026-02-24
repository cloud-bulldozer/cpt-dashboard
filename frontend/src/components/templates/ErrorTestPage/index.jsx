import React from 'react';
import { Button, Card, CardBody, CardHeader, Grid, GridItem } from '@patternfly/react-core';
import axiosInstance from '@/utils/axiosInstance';

/**
 * TEMPORARY TEST PAGE FOR ERROR HANDLING - REMOVE AFTER TESTING
 * 
 * This page provides buttons to test different error response formats
 * from the backend to verify the enhanced axios error handling works correctly.
 */
const ErrorTestPage = () => {
  const testEndpoints = [
    {
      name: 'Format 1: {"detail": {"message": "..."}}',
      url: '/api/v1/ocp/test-errors/format1',
      description: 'Tests HTTPException with message object format'
    },
    {
      name: 'Format 2: {"detail": {"error": "..."}}',
      url: '/api/v1/ocp/test-errors/format2',
      description: 'Tests HTTPException with error object format'
    },
    {
      name: 'Format 3: {"detail": "..."}',
      url: '/api/v1/ocp/test-errors/format3',
      description: 'Tests HTTPException with string detail format'
    },
    {
      name: 'Format 4: {"error": "..."}',
      url: '/api/v1/ocp/test-errors/format4',
      description: 'Tests direct error key format'
    },
    {
      name: 'Malformed Response',
      url: '/api/v1/ocp/test-errors/malformed',
      description: 'Tests non-JSON response handling'
    },
    {
      name: 'Network Timeout',
      url: '/api/v1/ocp/test-errors/network',
      description: 'Tests network timeout handling (will take 30s to timeout)'
    },
    {
      name: 'Validation Errors',
      url: '/api/v1/ocp/test-errors/validation',
      description: 'Tests FastAPI validation error format with array of error objects'
    }
  ];

  const handleTestError = async (endpoint) => {
    try {
      console.log(`Testing endpoint: ${endpoint.url}`);
      await axiosInstance.get(endpoint.url);
      console.log('Unexpected success - this should have failed');
    } catch (error) {
      console.log(`Expected error caught for ${endpoint.url}:`, error);
      // The axios interceptor should have already shown the toast
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <Card>
        <CardHeader>
          <h1>Error Handling Test Page</h1>
          <p>
            <strong>TEMPORARY TEST PAGE - REMOVE AFTER TESTING</strong>
          </p>
          <p>
            Click the buttons below to test different error response formats.
            Each button will trigger a different type of error response from the backend.
            Check the toast notifications to verify the error handling works correctly.
          </p>
        </CardHeader>
        <CardBody>
          <Grid hasGutter>
            {testEndpoints.map((endpoint, index) => (
              <GridItem key={index} span={6}>
                <Card isCompact>
                  <CardBody>
                    <h3>{endpoint.name}</h3>
                    <p style={{ fontSize: '14px', color: '#666', marginBottom: '10px' }}>
                      {endpoint.description}
                    </p>
                    <Button
                      variant="danger"
                      onClick={() => handleTestError(endpoint)}
                      style={{ width: '100%' }}
                    >
                      Test This Error
                    </Button>
                  </CardBody>
                </Card>
              </GridItem>
            ))}
          </Grid>
          
          <div style={{ marginTop: '30px', padding: '15px', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
            <h4>Testing Instructions:</h4>
            <ol>
              <li>Open the browser's developer console to see detailed error logs</li>
              <li>Click each button to test different error formats</li>
              <li>Verify that appropriate toast notifications appear for each error type</li>
              <li>Check that the UI remains operational after each error</li>
              <li>The "Network Timeout" test will take about 30 seconds to complete</li>
            </ol>
            <p style={{ marginTop: '10px', fontWeight: 'bold', color: '#d73502' }}>
              Remember to remove this test page and the temporary backend endpoints after testing!
            </p>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

export default ErrorTestPage;
