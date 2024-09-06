import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { H5, Progressbar } from '../../../../AbstractElements';
import { LargeProgressBars } from '../../../../Constant';

const Large = () => {
  return (
    <Card>
      <CardHeader>
        <H5>{LargeProgressBars}</H5><span>{'Use'} <code> {'.lg-progress-bar'}</code>{'class to change progress size to small:'}</span>
      </CardHeader>
      <CardBody>
        <div className="progress-showcase row">
          <Col>
            <Progressbar attrProgress={{ color: 'primary', value: '25', className: 'lg-progress-bar' }} />
            <Progressbar attrProgress={{ color: 'secondary', value: '50', className: 'lg-progress-bar' }} />
            <Progressbar attrProgress={{ color: 'success', value: '75', className: 'lg-progress-bar' }} />
            <Progressbar attrProgress={{ color: 'info', value: '100', className: 'lg-progress-bar' }} />
          </Col>
        </div>
      </CardBody>
    </Card>
  );
};

export default Large;