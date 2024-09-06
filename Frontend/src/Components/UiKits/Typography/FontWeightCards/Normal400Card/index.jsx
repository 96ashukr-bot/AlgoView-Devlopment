import React from 'react';
import { Fragment } from 'react';
import { Card, CardBody, CardHeader } from 'reactstrap';
import { H1, H2, H3, H4, H5, H6 } from '../../../../../AbstractElements';
import { Heading1, Heading2, Heading3, Heading4, Heading5, Heading6, Normal400 } from '../../../../../Constant';

const Normal400Card = () => {
  return (
    <Fragment>
      <Card>
        <CardHeader>
          <H5>{Normal400}</H5>
        </CardHeader>
        <CardBody className="typography">
          <H1 attrH1={{ className: 'f-w-400' }}>{Heading1}</H1>
          <H2 attrH2={{ className: 'f-w-400' }}>{Heading2}</H2>
          <H3 attrH3={{ className: 'f-w-400' }}>{Heading3}</H3>
          <H4 attrH4={{ className: 'f-w-400' }}>{Heading4}</H4>
          <H5 attrH5={{ className: 'f-w-400' }}>{Heading5}</H5>
          <H6 attrH6={{ className: 'f-w-400' }}>{Heading6}</H6>
        </CardBody>
      </Card>
    </Fragment>
  );

};
export default Normal400Card;