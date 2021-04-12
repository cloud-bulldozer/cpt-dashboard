import React from 'react';
import { JumpLinks, JumpLinksItem } from '@patternfly/react-core';

const VersionLinks = (props) => {
	return (
	    <JumpLinks>
	      {props.data.map((t) => (
	        <JumpLinksItem key={t.version} href={`#${t.version}`}>
	          {t.version}
	        </JumpLinksItem>
	      ))}
	    </JumpLinks>
	);
}

export default VersionLinks;