import React from 'react';
import { JumpLinks, JumpLinksItem } from '@patternfly/react-core';

const WithLabels = (props) => {
	return (
	    <JumpLinks label="jump to version">
	      {props.data.map((t) => (
	        <JumpLinksItem key={t.version} href={`#${t.version}`}>
	          {t.version}
	        </JumpLinksItem>
	      ))}
	    </JumpLinks>
	);
}

export default WithLabels;