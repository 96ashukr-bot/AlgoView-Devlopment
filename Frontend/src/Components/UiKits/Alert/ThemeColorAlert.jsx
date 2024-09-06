import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { Alerts, H5 } from '../../../AbstractElements';

const ThemeColorAlert = () => {
  return (
    <Col sm="12" xl="6">
      <Card>
        <CardHeader>
          <H5>{'Theme Color Alerts'}</H5><span>{'Theme color Archive just adding class'} <code>{'.dark'}</code></span>
        </CardHeader>
        <CardBody>
          <Alerts attrAlert={{ color: 'primary dark' }}>
            {'This is a info alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'secondary dark' }} >
            {'This is a light alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'success dark' }} >
            {'This is a success alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'info dark' }} >
            {'This is a danger alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'warning dark' }} >
            {'This is a secondary alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'danger dark' }} >
            {'This is a warning alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'light dark' }} >
            {'This is a dark alert—check it out!'}
          </Alerts>
          <Alerts attrAlert={{ color: 'dark dark' }} >
            {'This is a dark alert—check it out!'}
          </Alerts>
        </CardBody>
      </Card>
    </Col>
  );
};

export default ThemeColorAlert;