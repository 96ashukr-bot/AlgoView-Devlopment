import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { H5, Progressbar } from '../../../../AbstractElements';
import { CustomHeightProgressBars } from '../../../../Constant';

const Custom = () => {
  return (
    <Card>
      <CardHeader>
        <H5>{CustomHeightProgressBars}</H5><span>{'Set a height value on the'} <code>{'.progress-bar'}</code>{', so if you change that value the outer'} <code>{'.progress'} </code> {'will automatically resize accordingly.'}</span>
      </CardHeader>
      <CardBody>
        <div className=" progress-showcase row">
          <Col>
            <Progressbar attrProgress={{ color: 'primary', value: '25', className: 'xs-progress-bar' }} />
            <Progressbar attrProgress={{ color: 'secondary', value: '50', className: 'sm-progress-bar' }} />
            <Progressbar attrProgress={{ color: 'success', value: '75', className: 'md-progress-bar' }} />
            <Progressbar attrProgress={{ color: 'info', value: '100', className: 'lg-progress-bar' }} />
          </Col>
        </div>
      </CardBody>
    </Card>
  );
};

export default Custom;