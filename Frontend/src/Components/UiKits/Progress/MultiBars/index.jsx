import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { H5, Progressbar } from '../../../../AbstractElements';
import { MultipleBars } from '../../../../Constant';

const MultiBars = () => {

  return (
    <Card>
      <CardHeader>
        <H5>{MultipleBars}</H5><span>{'Include multiple progress bars in a progress component if you need.'}</span>
      </CardHeader>
      <CardBody>
        <div className="progress-showcase row">
          <Col>
            <Progressbar attrProgress={{ multi: true }}>
              <Progressbar attrProgress={{ bar: true, color: 'primary', value: '30' }} />
              <Progressbar attrProgress={{ bar: true, color: 'secondary', value: '20' }} />
              <Progressbar attrProgress={{ bar: true, color: 'success', value: '15' }} />
            </Progressbar>
            <Progressbar attrProgress={{ multi: true }}>
              <Progressbar attrProgress={{ bar: true, color: 'primary', value: '10' }} />
              <Progressbar attrProgress={{ bar: true, color: 'secondary', value: '10' }} />
              <Progressbar attrProgress={{ bar: true, color: 'success', value: '10' }} />
              <Progressbar attrProgress={{ bar: true, color: 'info', value: '10' }} />
              <Progressbar attrProgress={{ bar: true, color: 'warning', value: '10' }} />
              <Progressbar attrProgress={{ bar: true, color: 'danger', value: '10' }} />
              <Progressbar attrProgress={{ bar: true, color: 'primary', value: '10' }} />
              <Progressbar attrProgress={{ bar: true, color: 'light', value: '10' }} />
            </Progressbar>
          </Col>
        </div>
      </CardBody>
    </Card>
  );

};

export default MultiBars;