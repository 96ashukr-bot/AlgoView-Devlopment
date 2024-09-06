import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { H5, Progressbar } from '../../../../AbstractElements';
import { ProgressBarsAnimated } from '../../../../Constant';

const Animated = () => {
  return (
    <Card>
      <CardHeader>
        <H5>{ProgressBarsAnimated}</H5><span>{'The striped gradient can also be animated. Add'} <code>{'.progress-bar-animated'}</code> {'to'} <code>{'.progress-bar'} </code> {'to animate the stripes right to left via CSS3 animations.'}</span>
      </CardHeader>
      <CardBody>
        <div  className="progress-showcase row">
          <Col>
            <Progressbar attrProgress={{ color: 'primary', value: '10', animated: true }} />
            <Progressbar attrProgress={{ color: 'secondary', value: '25', animated: true }} />
            <Progressbar attrProgress={{ color: 'success', value: '50', animated: true }} />
            <Progressbar attrProgress={{ color: 'info', value: '75', animated: true }} />
          </Col>
        </div>
      </CardBody>
    </Card>
  );
};

export default Animated;