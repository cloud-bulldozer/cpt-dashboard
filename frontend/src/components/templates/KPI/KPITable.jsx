import { Table, Tbody, Td, Th, Thead, Tr } from "@patternfly/react-table";
import { useState, useMemo } from "react";
import PropTypes from "prop-types";
import KPIBenchmarkExpandedRow from "./KPIBenchmarkExpandedRow";

const KPITable = ({ data }) => {
  const [expandedVersions, setExpandedVersions] = useState(new Set());
  const [expandedBenchmarks, setExpandedBenchmarks] = useState(new Set());

  // Transform the data structure for easier rendering
  const tableData = useMemo(() => {
    if (!data?.metrics) return [];

    return Object.entries(data.metrics).map(([version, benchmarks]) => ({
      version,
      benchmarks: Object.entries(benchmarks).map(
        ([benchmarkName, configs]) => ({
          benchmarkName,
          configs: Object.entries(configs).map(([configKey, iterations]) => ({
            configKey,
            configName: data.config_key?.[configKey] || configKey,
            iterations: Object.entries(iterations).map(
              ([iterationCount, iterationData]) => ({
                iterationCount,
                ...iterationData,
              }),
            ),
          })),
        }),
      ),
    }));
  }, [data]);

  const toggleVersionExpansion = (version) => {
    const newExpanded = new Set(expandedVersions);
    if (newExpanded.has(version)) {
      newExpanded.delete(version);
    } else {
      newExpanded.add(version);
    }
    setExpandedVersions(newExpanded);
  };

  const toggleBenchmarkExpansion = (version, benchmarkName) => {
    const key = `${version}-${benchmarkName}`;
    const newExpanded = new Set(expandedBenchmarks);
    if (newExpanded.has(key)) {
      newExpanded.delete(key);
    } else {
      newExpanded.add(key);
    }
    setExpandedBenchmarks(newExpanded);
  };

  const isVersionExpanded = (version) => expandedVersions.has(version);
  const isBenchmarkExpanded = (version, benchmarkName) =>
    expandedBenchmarks.has(`${version}-${benchmarkName}`);

  const renderRows = () => {
    const rows = [];

    tableData.forEach((versionData) => {
      const totalConfigs = versionData.benchmarks.reduce(
        (sum, benchmark) => sum + benchmark.configs.length,
        0,
      );

      // Version row
      rows.push(
        <Tr key={versionData.version} data-level="0">
          <Td
            expand={{
              rowIndex: versionData.version,
              isExpanded: isVersionExpanded(versionData.version),
              onToggle: () => toggleVersionExpansion(versionData.version),
            }}
          />
          <Td dataLabel="Version">{versionData.version}</Td>
          <Td dataLabel="Benchmarks Count">{versionData.benchmarks.length}</Td>
          <Td dataLabel="Total Configurations">{totalConfigs}</Td>
        </Tr>,
      );

      // Benchmark rows (when version is expanded)
      if (isVersionExpanded(versionData.version)) {
        versionData.benchmarks.forEach((benchmark) => {
          rows.push(
            <Tr
              key={`${versionData.version}-${benchmark.benchmarkName}`}
              data-level="1"
            >
              <Td
                expand={{
                  rowIndex: `${versionData.version}-${benchmark.benchmarkName}`,
                  isExpanded: isBenchmarkExpanded(
                    versionData.version,
                    benchmark.benchmarkName,
                  ),
                  onToggle: () =>
                    toggleBenchmarkExpansion(
                      versionData.version,
                      benchmark.benchmarkName,
                    ),
                }}
              />
              <Td dataLabel="Benchmark">{benchmark.benchmarkName}</Td>
              <Td dataLabel="Configurations">{benchmark.configs.length}</Td>
              <Td dataLabel="Total Iterations">
                {benchmark.configs.reduce(
                  (sum, config) => sum + config.iterations.length,
                  0,
                )}
              </Td>
            </Tr>,
          );

          // Configuration row (when benchmark is expanded) - show single row with dropdowns
          if (
            isBenchmarkExpanded(versionData.version, benchmark.benchmarkName)
          ) {
            rows.push(
              <KPIBenchmarkExpandedRow
                key={`${versionData.version}-${benchmark.benchmarkName}-expanded`}
                benchmark={benchmark.benchmarkName}
                configs={benchmark.configs}
              />,
            );
          }
        });
      }
    });

    return rows;
  };

  return (
    <Table isStriped ouiaId="kpi_data_table">
      <Thead>
        <Tr>
          <Th />
          <Th>Version</Th>
          <Th>Benchmarks Count</Th>
          <Th>Total Configurations</Th>
        </Tr>
      </Thead>
      <Tbody>{renderRows()}</Tbody>
    </Table>
  );
};

KPITable.propTypes = {
  data: PropTypes.object.isRequired,
};

export default KPITable;
