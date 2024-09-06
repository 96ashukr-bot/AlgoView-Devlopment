import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { Alerts, H5 } from '../../../AbstractElements';
import { OutlineAlerts } from '../../../Constant';

const OutlineAlert = () => {
  return (
    <Col sm="12" xl="6">
      <Card className="card height-equal" style={{ minHeight: '708px' }}>
        <CardHeader>
          <H5>{OutlineAlerts}</H5><span>{'Outline Archive just adding class'} <code>{'.outline'}</code></span>
        </CardHeader>
        <CardBody>
          <Alerts attrAlert={{ color: 'primary outline' }}>
            {'This is a info alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'secondary outline' }} >
            {'This is a light alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'success outline' }} >
            {'This is a success alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'info outline' }} >
            {'This is a danger alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'warning outline' }} >
            {'This is a secondary alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'danger outline' }} >
            {'This is a warning alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'light outline' }} >
            {'This is a dark alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'dark outline' }} >
            {'This is a dark alert—check it out!'}
          </Alerts>
        </CardBody>
      </Card>
    </Col>
  );
};

export default OutlineAlert;