import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { Badges, H1, H2, H3, H4, H5, H6 } from '../../../AbstractElements';
import { BadgesExample, New } from '../../../Constant';

const BadgeExample = () => {
  return (
    <Col sm="12" xl="6">
      <Card className="height-equal">
        <CardHeader>
          <H5>{BadgesExample}</H5>
        </CardHeader>
        <CardBody>
          <H1>{'heading'} <Badges attrBadge={{ color: 'primary' }} >{New}</Badges></H1>
          <H2>{'heading'} <Badges attrBadge={{ color: 'primary' }} >{New}</Badges></H2>
          <H3>{'heading'} <Badges attrBadge={{ color: 'primary' }} >{New}</Badges></H3>
          <H4>{'heading'} <Badges attrBadge={{ color: 'primary' }} >{New}</Badges></H4>
          <H5>{'heading'} <Badges attrBadge={{ color: 'primary' }} >{New}</Badges></H5>
          <H6>{'heading'} <Badges attrBadge={{ color: 'primary' }} >{New}</Badges></H6>
        </CardBody>
      </Card>
    </Col>
  );
};

export default BadgeExample;