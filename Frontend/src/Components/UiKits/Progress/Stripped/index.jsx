import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { H5, Progressbar } from '../../../../AbstractElements';
import { ProgressBarsStriped } from '../../../../Constant';

const Striped = () => {
  return (
    <Card>
      <CardHeader>
        <H5>{ProgressBarsStriped}</H5><span>{'Add'} <code>{'.progress-bar-striped'}</code> {'to any'} <code>{'.progress-bar'}</code> {'to apply a stripe via CSS gradient over the progress bar’s background color.'}</span>
      </CardHeader>
      <CardBody>
        <div className="progress-showcase row">
          <Col>
            <Progressbar attrProgress={{ color: 'primary', value: '10', striped: true }} />
            <Progressbar attrProgress={{ color: 'secondary', value: '25', striped: true }} />
            <Progressbar attrProgress={{ color: 'success', value: '50', striped: true }} />
            <Progressbar attrProgress={{ color: 'info', value: '75', striped: true }} />
          </Col>
        </div>
      </CardBody>
    </Card>
  );
};

export default Striped;