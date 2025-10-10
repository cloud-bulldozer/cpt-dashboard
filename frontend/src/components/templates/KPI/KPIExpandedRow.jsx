import {
  Card,
  CardBody,
  Grid,
  GridItem,
  Title,
  DescriptionList,
  DescriptionListTerm,
  DescriptionListDescription,
  DescriptionListGroup,
} from "@patternfly/react-core";
import { Td, Tr } from "@patternfly/react-table";
import PropTypes from "prop-types";
import PlotGraph from "@/components/atoms/PlotGraph";

const KPIExpandedRow = ({ version, benchmark, config }) => {
  // Format configuration details for display
  const formatConfigDetails = (configData) => {
    if (!configData) return "Unknown Configuration";
    
    const details = [];
    if (configData.platform) details.push(`Platform: ${configData.platform}`);
    if (configData.masterNodesType) details.push(`Master: ${configData.masterNodesType} (${configData.masterNodesCount})`);
    if (configData.workerNodesType) details.push(`Worker: ${configData.workerNodesType} (${configData.workerNodesCount})`);
    
    return details.length > 0 ? details.join(", ") : config.configKey;
  };

  const formatStatValue = (value) => {
    if (value === null || value === undefined) return "N/A";
    if (typeof value === "number") return value.toLocaleString();
    return value;
  };

  return (
    <Tr data-level="2">
      <Td />
      <Td colSpan={3} style={{ padding: "1rem 2rem" }}>
        <div className="kpi-expanded-content">
        <Card>
          <CardBody>
            <Title headingLevel="h4" size="lg" style={{ marginBottom: "1rem" }}>
              Configuration: {formatConfigDetails(config.configName)}
            </Title>
            
            <Grid hasGutter>
              {config.iterations.map((iteration) => (
                <GridItem span={12} key={iteration.iterationCount}>
                  <Card>
                    <CardBody>
                      <Title headingLevel="h5" size="md" style={{ marginBottom: "1rem" }}>
                        Iteration Count: {iteration.iterationCount}
                      </Title>
                      
                      <Grid hasGutter>
                        {/* Statistics Section */}
                        <GridItem span={6}>
                          <div className="stats-section">
                          <Title headingLevel="h6" size="sm" style={{ marginBottom: "0.5rem" }}>
                            Statistics
                          </Title>
                          <DescriptionList isHorizontal isCompact>
                            <DescriptionListGroup>
                              <DescriptionListTerm>Minimum</DescriptionListTerm>
                              <DescriptionListDescription>
                                {formatStatValue(iteration.stats?.min)}
                              </DescriptionListDescription>
                            </DescriptionListGroup>
                            <DescriptionListGroup>
                              <DescriptionListTerm>Maximum</DescriptionListTerm>
                              <DescriptionListDescription>
                                {formatStatValue(iteration.stats?.max)}
                              </DescriptionListDescription>
                            </DescriptionListGroup>
                            <DescriptionListGroup>
                              <DescriptionListTerm>Average</DescriptionListTerm>
                              <DescriptionListDescription>
                                {formatStatValue(iteration.stats?.avg)}
                              </DescriptionListDescription>
                            </DescriptionListGroup>
                            <DescriptionListGroup>
                              <DescriptionListTerm>Std Deviation</DescriptionListTerm>
                              <DescriptionListDescription>
                                {formatStatValue(iteration.stats?.std_dev)}
                              </DescriptionListDescription>
                            </DescriptionListGroup>
                          </DescriptionList>
                          
                          {/* Values List */}
                          {iteration.values && iteration.values.length > 0 && (
                            <>
                              <Title headingLevel="h6" size="sm" style={{ marginTop: "1rem", marginBottom: "0.5rem" }}>
                                Individual Values ({iteration.values.length} runs)
                              </Title>
                              <div className="values-list">
                                {iteration.values.map((valueData, index) => (
                                  <div key={valueData.uuid || index} className="value-item">
                                    <span className="value">{valueData.value?.toLocaleString()}</span>
                                    {valueData.timestamp && (
                                      <span className="timestamp">
                                        ({new Date(valueData.timestamp).toLocaleString()})
                                      </span>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </>
                          )}
                          </div>
                        </GridItem>
                        
                        {/* Chart Section */}
                        <GridItem span={6}>
                          <div className="chart-section">
                          <Title headingLevel="h6" size="sm" style={{ marginBottom: "0.5rem" }}>
                            Performance Chart
                          </Title>
                          {iteration.graph && iteration.graph.x && iteration.graph.x.length > 0 ? (
                            <PlotGraph data={[iteration.graph]} />
                          ) : (
                            <div className="no-data-placeholder">
                              No chart data available
                            </div>
                          )}
                          </div>
                        </GridItem>
                      </Grid>
                    </CardBody>
                  </Card>
                </GridItem>
              ))}
            </Grid>
          </CardBody>
        </Card>
        </div>
      </Td>
    </Tr>
  );
};

KPIExpandedRow.propTypes = {
  version: PropTypes.string.isRequired,
  benchmark: PropTypes.string.isRequired,
  config: PropTypes.object.isRequired,
};

export default KPIExpandedRow;
