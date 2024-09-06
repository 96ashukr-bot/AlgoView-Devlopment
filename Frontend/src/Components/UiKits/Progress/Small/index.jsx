import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { H5, Progressbar } from '../../../../AbstractElements';
import { SmallProgressBars } from '../../../../Constant';

const Small = () => {
  return (
    <Card>
      <CardHeader>
        <H5>{SmallProgressBars}</H5><span>{'Use'} <code> {'.sm-progress-bar'}</code>{'class to change progress size to small:'}</span>
      </CardHeader>
      <CardBody>
        <div className="progress-showcase row">
          <Col>
            <Progressbar attrProgress={{ value: '25', color: 'primary', className: 'sm-progress-bar' }} />
            <Progressbar attrProgress={{ color: 'secondary', value: '50', className: 'sm-progress-bar' }} />
            <Progressbar attrProgress={{ color: 'success', value: '75', className: 'sm-progress-bar' }} />
            <Progressbar attrProgress={{ color: 'info', value: '100', className: 'sm-progress-bar' }} />
          </Col>
        </div>
      </CardBody>
    </Card>
  );
};

export default Small;