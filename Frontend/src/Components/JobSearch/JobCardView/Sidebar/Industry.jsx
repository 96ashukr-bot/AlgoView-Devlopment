import { Btn, H5 } from '../../../../AbstractElements';
import React, { Fragment, useState } from 'react';
import { Card, CardBody, CardHeader, Col, Collapse, Input, Label } from 'reactstrap';

const Industry = () => {
  const [isFilter, setIsFilter] = useState(true);
  return (
    <Fragment>
      <Col xl='12'>
        <Card>
          <CardHeader>
            <H5 attrH5={{ className: 'mb-0 p-0' }}>
              <Btn attrBtn={{ className: 'btn btn-link ', onClick: () => setIsFilter(!isFilter), color: 'transperant' }}>Industry</Btn>
            </H5>
          </CardHeader>
          <Collapse isOpen={isFilter}>
            <CardBody className='animate-chk'>
              <Label className='d-block' for='chk-ani16'>
                <Input className='checkbox_animated' id='chk-ani16' type='checkbox' /> Computer Software(14)
              </Label>
              <Label className='d-block' for='chk-ani17'>
                <Input className='checkbox_animated' id='chk-ani17' type='checkbox' /> IT Engineer(10)
              </Label>
              <Label className='d-block' for='chk-ani18'>
                <Input className='checkbox_animated' id='chk-ani18' type='checkbox' /> Service industry(20)
              </Label>
              <Label className='d-block' for='chk-ani19'>
                <Input className='checkbox_animated' id='chk-ani19' type='checkbox' /> Accounting(34)
              </Label>
              <Label className='d-block mb-0' for='chk-ani20'>
                <Input className='checkbox_animated' id='chk-ani20' type='checkbox' /> Financial Services(5)
              </Label>
            </CardBody>
            <Btn attrBtn={{ className: 'btn d-block w-100  text-center', color: 'primary', type: 'button' }}>All Industries</Btn>
          </Collapse>
        </Card>
      </Col>
    </Fragment>
  );
};

export default Industry;
