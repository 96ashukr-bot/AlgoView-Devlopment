import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { H1, H5 } from '../../../../AbstractElements';
import { DisplayHeadings } from '../../../../Constant';

const DisplayHeadingCard = () => {
  return (
    <Col sm="12">
      <Card>
        <CardHeader>
          <H5>{DisplayHeadings}</H5><span>{'Traditional heading elements are designed to work best in the meat of your page content. When you need a heading to stand out, consider using a'} <strong>{'display heading'}</strong>{'—a larger, slightly more opinionated heading style.'}</span>
        </CardHeader>
        <CardBody className="typography">
          <H1 attrH1={{ className: 'display-1' }}>{'Display 1'}</H1>
          <H1 attrH1={{ className: 'display-2' }}>{'Display 2'}</H1>
          <H1 attrH1={{ className: 'display-3' }}>{'Display 3'}</H1>
          <H1 attrH1={{ className: 'display-4' }}>{'Display 4'}</H1>
        </CardBody>
      </Card>
    </Col>
  );
};

export default DisplayHeadingCard;