import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { H5, P } from '../../../../AbstractElements';

const LeadCard = () =>{
    return(
      <Col sm="12">
        <Card>
          <CardHeader>
            <H5>{'Lead'}</H5><span>{'Make a paragraph stand out by adding'} <code>{'.lead'}</code>.</span>
          </CardHeader>
          <CardBody>
            <P attrPara={{ className:'lead' }}>{'Vivamus sagittis lacus vel augue laoreet rutrum faucibus dolor auctor. Duis mollis, est non commodo luctus.'}</P>
          </CardBody>
        </Card>
      </Col>
    );
};

export default LeadCard;