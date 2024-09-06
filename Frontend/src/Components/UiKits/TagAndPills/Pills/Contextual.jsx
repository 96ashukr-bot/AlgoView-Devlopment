import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { Badges, H5 } from '../../../../AbstractElements';
import { ContextualVariations, Danger, Dark, Info, Light, Primary, secondary, Success, Warning } from '../../../../Constant';

const ContextualPills = () => {
  return (
    <Col sm="12" xl="6">
      <Card>
        <CardHeader>
          <H5>{ContextualVariations}</H5>
        </CardHeader>
        <CardBody>
          <Badges attrBadge={{ className: 'badge rounded-pill', color: 'primary', pill: true }}>{Primary}</Badges>
          <Badges attrBadge={{ className: 'badge rounded-pill', color: 'secondary', pill: true }} >{secondary}</Badges>
          <Badges attrBadge={{ className: 'badge rounded-pill', color: 'success', pill: true }} >{Success}</Badges>
          <Badges attrBadge={{ className: 'badge rounded-pill', color: 'info', pill: true }} >{Info}</Badges>
          <Badges attrBadge={{ className: 'badge rounded-pill', color: 'warning', pill: true }}>{Warning}</Badges>
          <Badges attrBadge={{ className: 'badge rounded-pill', color: 'danger', pill: true }} >{Danger}</Badges>
          <Badges attrBadge={{ className: 'badge rounded-pill txt-dark', color: 'light', pill: true }} >{Light}</Badges>
          <Badges attrBadge={{ className: 'badge rounded-pill', color: 'dark tag-pills-sm-mb', pill: true }} >{Dark}</Badges>
        </CardBody>
      </Card>
    </Col>
  );
};

export default ContextualPills;