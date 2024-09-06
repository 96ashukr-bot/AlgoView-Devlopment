import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { Badges, H5 } from '../../../../AbstractElements';
import { ContextualVariations, Danger, Dark, Light, Primary, secondary, Success, Warning, Info } from '../../../../Constant';

const ContextualBadge = () => {
  return (
    <Col sm="12" xl="6">
      <Card>
        <CardHeader>
          <H5>{ContextualVariations}</H5>
        </CardHeader>
        <CardBody>
          <Badges attrBadge={{ color: 'primary' }} >{Primary}</Badges><Badges attrBadge={{ color: 'secondary' }}>{secondary}</Badges>
          <Badges attrBadge={{ color: 'success' }}>{Success}</Badges><Badges attrBadge={{ color: 'info' }}>{Info}</Badges>
          <Badges attrBadge={{ color: 'warning' }}>{Warning}</Badges><Badges attrBadge={{ color: 'danger' }}>{Danger}</Badges>
          <Badges attrBadge={{ color: 'light txt-dark' }}>{Light}</Badges><Badges attrBadge={{ color: 'dark tag-pills-sm-mb' }}>{Dark}</Badges>
        </CardBody>
      </Card>
    </Col>
  );
};

export default ContextualBadge;