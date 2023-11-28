
export const OCP_INITIAL_DATA = {
    initialState: true,
    success: 0,
    failure: 0,
    total: 0,
    others: 0,
    duration:0,
    benchmarks: ["All"],
    versions: ["All"],
    workers: ["All"],
    ciSystems: ["All"],
    networkTypes: ["All"],
    jobTypes: ["All"],
    rehearses: ["All"],
    selectedBenchmark: "All",
    selectedVersion: "All",
    selectedPlatform: "All",
    selectedWorkerCount: "All",
    selectedNetworkType: "All",
    selectedCiSystem: "All",
    selectedJobType: "All",
    selectedRehearse: "All",
    waitForUpdate: false,
    platforms: ["All"],
    copyData: [],
    data: [],
    updatedTime: 'Loading',
    error: null,
    startDate: '',
    endDate: '',
    tableData : [{ name: "Benchmark", value: "benchmark" },
                {name:"ReleaseStream", value: "releaseStream"},
                {name: "WorkerCount", value: "workerNodesCount"},
                {name: "StartDate", value: "startDate"},
                {name: "EndDate", value: "endDate"},
                {name: "Status", value: "jobStatus"}],
}

export const CPT_INITIAL_DATA = {
    initialState: true,
    success: 0,
    failure: 0,
    total: 0,
    others: 0,
    testNames: ["All"],
    products: ["All"],
    ciSystems: ["All"],
    statuses: ["All"],
    releaseStreams: ["All"],
    selectedCiSystem: "All",
    selectedProduct: "All",
    selectedTestName: "All",
    selectedJobStatus: "All",
    selectedReleaseStream: "All",
    waitForUpdate: false,
    copyData: [],
    data: [],
    updatedTime: 'Loading',
    error: null,
    startDate: '',
    endDate: '',
    tableData : [{name:"Product", value: "product"},
                { name: "CI System", value: "ciSystem" },
                {name: "Test Name", value: "testName"},
                {name: "Version", value: "version"},
                {name: "Release Stream", value: "releaseStream"},
                {name: "Start Date", value: "startDate"},
                {name: "End Date", value: "endDate"},
                {name: "Build URL", value: "buildUrl"},
                {name: "Status", value: "jobStatus"},],
}

export const GRAPH_INITIAL_DATA = {
    uuid_results: {},
    graphError: false,
}
