import React from 'react';
import VersionDf from './VersionDf';

const VersionList = (props) => {
	return (
	  props.data.map((t) => (
	      <VersionDf 
	        key={t.version}
	        version={t.version}
	        data={t.cloud_data} />
	  ))
	);
}

export default VersionList;