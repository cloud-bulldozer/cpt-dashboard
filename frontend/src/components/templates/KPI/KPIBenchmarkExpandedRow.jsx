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
  Select,
  SelectList,
  SelectOption,
  MenuToggle,
} from "@patternfly/react-core";
import { Td, Tr } from "@patternfly/react-table";
import { useState } from "react";
import PropTypes from "prop-types";
import PlotGraph from "@/components/atoms/PlotGraph";

const KPIBenchmarkExpandedRow = ({ benchmark, configs }) => {
  const [selectedConfigKey, setSelectedConfigKey] = useState(
    configs[0]?.configKey || "",
  );
  const [selectedIterationCount, setSelectedIterationCount] = useState("");
  const [isConfigSelectOpen, setIsConfigSelectOpen] = useState(false);
  const [isIterationSelectOpen, setIsIterationSelectOpen] = useState(false);

  // Get the selected configuration
  const selectedConfig =
    configs.find((config) => config.configKey === selectedConfigKey) ||
    configs[0];

  // Get available iteration counts for the selected configuration
  const availableIterations = selectedConfig?.iterations || [];

  // Set default iteration if not selected
  if (!selectedIterationCount && availableIterations.length > 0) {
    setSelectedIterationCount(availableIterations[0].iterationCount);
  }

  // Get the selected iteration data
  const selectedIteration =
    availableIterations.find(
      (iteration) => iteration.iterationCount === selectedIterationCount,
    ) || availableIterations[0];

  // Format configuration details for display
  const formatConfigDetails = (configData) => {
    if (!configData) return "Unknown Configuration";

    const details = [];
    if (configData.platform) details.push(`Platform: ${configData.platform}`);
    if (configData.masterNodesType)
      details.push(
        `Master: ${configData.masterNodesType} (${configData.masterNodesCount})`,
      );
    if (configData.workerNodesType)
      details.push(
        `Worker: ${configData.workerNodesType} (${configData.workerNodesCount})`,
      );

    return details.length > 0 ? details.join(", ") : selectedConfig.configKey;
  };

  const formatStatValue = (value) => {
    if (value === null || value === undefined) return "N/A";
    if (typeof value === "number") return value.toLocaleString();
    return value;
  };

  const handleConfigSelect = (_event, value) => {
    setSelectedConfigKey(value);
    setIsConfigSelectOpen(false);
    // Reset iteration selection when config changes
    const newConfig = configs.find((config) => config.configKey === value);
    if (newConfig && newConfig.iterations.length > 0) {
      setSelectedIterationCount(newConfig.iterations[0].iterationCount);
    }
  };

  const handleIterationSelect = (_event, value) => {
    setSelectedIterationCount(value);
    setIsIterationSelectOpen(false);
  };

  const configToggle = (toggleRef) => (
    <MenuToggle
      ref={toggleRef}
      onClick={() => setIsConfigSelectOpen(!isConfigSelectOpen)}
      isExpanded={isConfigSelectOpen}
      style={{ width: "300px" }}
    >
      {selectedConfig
        ? `Config: ${selectedConfig.configKey}`
        : "Select Configuration"}
    </MenuToggle>
  );

  const iterationToggle = (toggleRef) => (
    <MenuToggle
      ref={toggleRef}
      onClick={() => setIsIterationSelectOpen(!isIterationSelectOpen)}
      isExpanded={isIterationSelectOpen}
      style={{ width: "200px" }}
    >
      {selectedIterationCount
        ? `Iterations: ${selectedIterationCount}`
        : "Select Iteration Count"}
    </MenuToggle>
  );

  return (
    <Tr data-level="2">
      <Td />
      <Td colSpan={3} style={{ padding: "1rem 2rem" }}>
        <div className="kpi-expanded-content">
          <Card>
            <CardBody>
              <Title
                headingLevel="h4"
                size="lg"
                style={{ marginBottom: "1rem" }}
              >
                Benchmark: {benchmark}
              </Title>

              {/* Configuration and Iteration Selectors */}
              <Grid
                hasGutter
                className="selector-grid"
                style={{ marginBottom: "1rem" }}
              >
                <GridItem span={6}>
                  <Title
                    headingLevel="h6"
                    size="sm"
                    style={{ marginBottom: "0.5rem" }}
                  >
                    Select Configuration:
                  </Title>
                  <Select
                    isOpen={isConfigSelectOpen}
                    selected={selectedConfigKey}
                    onSelect={handleConfigSelect}
                    onOpenChange={(isOpen) => setIsConfigSelectOpen(isOpen)}
                    toggle={configToggle}
                  >
                    <SelectList>
                      {configs.map((config) => (
                        <SelectOption
                          key={config.configKey}
                          value={config.configKey}
                        >
                          {config.configKey}
                        </SelectOption>
                      ))}
                    </SelectList>
                  </Select>
                </GridItem>

                {availableIterations.length > 1 && (
                  <GridItem span={6}>
                    <Title
                      headingLevel="h6"
                      size="sm"
                      style={{ marginBottom: "0.5rem" }}
                    >
                      Select Iteration Count:
                    </Title>
                    <Select
                      isOpen={isIterationSelectOpen}
                      selected={selectedIterationCount}
                      onSelect={handleIterationSelect}
                      onOpenChange={(isOpen) =>
                        setIsIterationSelectOpen(isOpen)
                      }
                      toggle={iterationToggle}
                    >
                      <SelectList>
                        {availableIterations.map((iteration) => (
                          <SelectOption
                            key={iteration.iterationCount}
                            value={iteration.iterationCount}
                          >
                            {iteration.iterationCount} iterations
                          </SelectOption>
                        ))}
                      </SelectList>
                    </Select>
                  </GridItem>
                )}
              </Grid>

              {/* Configuration Details */}
              <Title
                headingLevel="h5"
                size="md"
                style={{ marginBottom: "1rem" }}
              >
                Configuration: {formatConfigDetails(selectedConfig.configName)}
              </Title>

              {selectedIteration && (
                <Grid hasGutter>
                  {/* Statistics Section */}
                  <GridItem span={6}>
                    <div className="stats-section">
                      <Title
                        headingLevel="h6"
                        size="sm"
                        style={{ marginBottom: "0.5rem" }}
                      >
                        Statistics ({selectedIteration.iterationCount}{" "}
                        iterations)
                      </Title>
                      <DescriptionList isHorizontal>
                        <DescriptionListGroup>
                          <DescriptionListTerm>Minimum</DescriptionListTerm>
                          <DescriptionListDescription>
                            {formatStatValue(selectedIteration.stats?.min)}
                          </DescriptionListDescription>
                        </DescriptionListGroup>
                        <DescriptionListGroup>
                          <DescriptionListTerm>Maximum</DescriptionListTerm>
                          <DescriptionListDescription>
                            {formatStatValue(selectedIteration.stats?.max)}
                          </DescriptionListDescription>
                        </DescriptionListGroup>
                        <DescriptionListGroup>
                          <DescriptionListTerm>Average</DescriptionListTerm>
                          <DescriptionListDescription>
                            {formatStatValue(selectedIteration.stats?.avg)}
                          </DescriptionListDescription>
                        </DescriptionListGroup>
                        <DescriptionListGroup>
                          <DescriptionListTerm>
                            Std Deviation
                          </DescriptionListTerm>
                          <DescriptionListDescription>
                            {formatStatValue(selectedIteration.stats?.std_dev)}
                          </DescriptionListDescription>
                        </DescriptionListGroup>
                      </DescriptionList>

                      {/* Values List */}
                      {selectedIteration.values &&
                        selectedIteration.values.length > 0 && (
                          <>
                            <Title
                              headingLevel="h6"
                              size="sm"
                              style={{
                                marginTop: "1rem",
                                marginBottom: "0.5rem",
                              }}
                            >
                              Individual Values (
                              {selectedIteration.values.length} runs)
                            </Title>
                            <div className="values-list">
                              {selectedIteration.values.map(
                                (valueData, index) => (
                                  <div
                                    key={valueData.uuid || index}
                                    className="value-item"
                                  >
                                    <span className="value">
                                      {valueData.value?.toLocaleString()}
                                    </span>
                                    {valueData.timestamp && (
                                      <span className="timestamp">
                                        (
                                        {new Date(
                                          valueData.timestamp,
                                        ).toLocaleString()}
                                        )
                                      </span>
                                    )}
                                  </div>
                                ),
                              )}
                            </div>
                          </>
                        )}
                    </div>
                  </GridItem>

                  {/* Chart Section */}
                  <GridItem span={6}>
                    <div className="chart-section">
                      <Title
                        headingLevel="h6"
                        size="sm"
                        style={{ marginBottom: "0.5rem" }}
                      >
                        Performance Chart
                      </Title>
                      {selectedIteration.graph &&
                      selectedIteration.graph.x &&
                      selectedIteration.graph.x.length > 0 ? (
                        <PlotGraph data={[selectedIteration.graph]} />
                      ) : (
                        <div className="no-data-placeholder">
                          No chart data available
                        </div>
                      )}
                    </div>
                  </GridItem>
                </Grid>
              )}
            </CardBody>
          </Card>
        </div>
      </Td>
    </Tr>
  );
};

KPIBenchmarkExpandedRow.propTypes = {
  benchmark: PropTypes.string.isRequired,
  configs: PropTypes.array.isRequired,
};

export default KPIBenchmarkExpandedRow;
