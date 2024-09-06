import React from 'react';
import { Mail, DollarSign, Headphones, Link, GitHub, Award, Activity, Heart } from 'react-feather';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { Badges, H5 } from '../../../../AbstractElements';
import { PillsWithIcon } from '../../../../Constant';

const PillWithIcon = () => {

  return (
    <Col sm="12" xl="6">
      <Card>
        <CardHeader>
          <H5>{PillsWithIcon}</H5>
        </CardHeader>
        <CardBody className="pill-icon">
          <Badges attrBadge={{ className: 'badge rounded-pill', color: 'primary', href: '#javascript', pill: true }} ><DollarSign /></Badges>
          <Badges attrBadge={{ className: 'badge rounded-pill', color: 'secondary', href: '#javascript', pill: true }}><Headphones /></Badges>
          <Badges attrBadge={{ className: 'badge rounded-pill', color: 'success', href: '#javascript', pill: true }}><Link /></Badges>
          <Badges attrBadge={{ className: 'badge rounded-pill', color: 'info', href: '#javascript', pill: true }}><GitHub /></Badges>
          <Badges attrBadge={{ className: 'badge rounded-pill', color: 'warning', href: '#javascript', pill: true }}><Award /></Badges>
          <Badges attrBadge={{ className: 'badge rounded-pill', color: 'danger', href: '#javascript', pill: true }}><Activity /></Badges>
          <Badges attrBadge={{ className: 'badge rounded-pill txt-dark', color: 'light', href: '#javascript', pill: true }}><Heart /></Badges>
          <Badges attrBadge={{ className: 'badge rounded-pill', color: 'dark', href: '#javascript', pill: true }}><Mail /></Badges>
        </CardBody>
      </Card>
    </Col>
  );
};

export default PillWithIcon;