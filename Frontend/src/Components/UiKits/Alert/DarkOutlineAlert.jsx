import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { Alerts, H5 } from '../../../AbstractElements';
import { OutlineDarkAlerts } from '../../../Constant';

const DarkOutlineAlert = () => {
  return (
    <Col sm="12" xl="6">
      <Card className="card height-equal" style={{ minHeight: '708px' }}>
        <CardHeader>
          <H5>{OutlineDarkAlerts}</H5><span>{'Outline Archive just adding class'} <code>{'.outline-2x'}</code></span>
        </CardHeader>
        <CardBody>
          <Alerts attrAlert={{ color: 'primary outline-2x' }}>
            {'This is a info alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'secondary outline-2x' }} >
            {'This is a light alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'success outline-2x' }} >
            {'This is a success alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'info outline-2x' }} >
            {'This is a danger alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'warning outline-2x' }} >
            {'This is a secondary alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'danger outline-2x' }} >
            {'This is a warning alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'light outline-2x' }} >
            {'This is a dark alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'dark outline-2x' }} >
            {'This is a dark alert—check it out!'}
          </Alerts>
        </CardBody>
      </Card>
    </Col>
  );
};

export default DarkOutlineAlert;