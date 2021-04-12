import React from 'react';
import PerformanceEntry from './PerformanceEntry';

const PerformanceResults = (props) => {
	return (
		props.data.map((t) => (
			<PerformanceEntry
				key={t.version}
				version={t.version}
				data={t.cloud_data}
				columns={t.columns} />
		))
	);
}

export default PerformanceResults;