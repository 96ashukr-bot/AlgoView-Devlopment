import React from 'react';
import { Card, CardBody, Col } from 'reactstrap';
import { Alerts } from '../../../AbstractElements';
import { LightAlerts } from '../../../Constant';
import HeaderCard from '../../Common/Component/HeaderCard';

const LightAlert = () => {
  return (
    <Col sm="12" xl="6">
      <Card>
        <HeaderCard title={LightAlerts} span1={'Alerts are available for any length of text, as well as an optional dismiss button.'} />
        <CardBody>
          <Alerts attrAlert={{ color: 'primary' }}>
            {'This is a info alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'secondary' }} >
            {'This is a light alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'success' }} >
            {'This is a success alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'info' }} >
            {'This is a danger alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'warning' }} >
            {'This is a secondary alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'danger' }} >
            {'This is a warning alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'light' }} >
            {'This is a dark alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'dark' }} >
            {'This is a dark alert—check it out!'}
          </Alerts>
        </CardBody>
      </Card>
    </Col>
  );
};

export default LightAlert;