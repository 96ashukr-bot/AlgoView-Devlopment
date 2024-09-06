import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { Alerts, H5 } from '../../../AbstractElements';

const LinkColors = () => {
  return (
    <Col sm="12" xl="6">
      <Card>
        <CardHeader>
          <H5>{'Link color in theme-color'}</H5><span>{'Use the'} <code>{'.alert-link'}</code> {'utility class to quickly provide matching colored links within any alert'}</span>
        </CardHeader>
        <CardBody>
          <Alerts attrAlert={{ color: 'primary dark' }}>
            {'This is a primary alert with'} <a className="alert-link" href="#javascript">{'an example link'}</a>{'.Click It'}
          </Alerts>
          <Alerts attrAlert={{ color: 'secondary dark' }} >
            {'This is a secondary alert with'} <a className="alert-link" href="#javascript">{'an example link'}</a>{'.Click It'}
          </Alerts>
          <Alerts attrAlert={{ color: 'success dark' }} >
            {'This is a success alert with'} <a className="alert-link" href="#javascript">{'an example link'}</a>{'.Click It'}
          </Alerts>
          <Alerts attrAlert={{ color: 'info dark' }} >
            {'This is a info alert with'} <a className="alert-link" href="#javascript">{'an example link'}</a>{'.Click It'}
          </Alerts>
          <Alerts attrAlert={{ color: 'warning dark' }} >
            {'This is a warning alert with'} <a className="alert-link" href="#javascript">{'an example link'}</a>{'.Click It'}
          </Alerts>
          <Alerts attrAlert={{ color: 'danger dark' }} >
            {'This is a danger alert with'} <a className="alert-link" href="#javascript">{'an example link'}</a>{'.Click It'}
          </Alerts>
          <Alerts attrAlert={{ color: 'light dark' }} >
            {'This is a light alert with'} <a className="alert-link" href="#javascript">{'an example link'}</a>{'.Click It'}
          </Alerts>
          <Alerts attrAlert={{ color: 'dark dark' }} >
            {'This is a dark alert with'} <a className="alert-link" href="#javascript">{'an example link'}</a>{'.Click It'}
          </Alerts>
        </CardBody>
      </Card>
    </Col>
  );
};

export default LinkColors;