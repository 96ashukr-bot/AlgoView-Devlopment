import { Btn, H5 } from '../../../../AbstractElements';
import React, { Fragment, useState } from 'react';
import { Col, Card, CardHeader, CardBody, Label, Collapse, Input } from 'reactstrap';

const Location = () => {
  const [isFilter, setIsFilter] = useState(true);
  return (
    <Fragment>
      <Col xl='12'>
        <Card>
          <CardHeader>
            <H5 attrH5={{ className: 'mb-0 p-0' }}>
              <Btn attrBtn={{ className: 'btn btn-link', onClick: () => setIsFilter(!isFilter), color: 'transperant' }}>Location</Btn>
            </H5>
          </CardHeader>
          <Collapse isOpen={isFilter}>
            <CardBody className='animate-chk'>
              <div className='location-checkbox'>
                <Label className='d-block' for='chk-ani6'>
                  <Input className='checkbox_animated' id='chk-ani6' type='checkbox' /> New York<span className='d-block'>NY (399)</span>
                </Label>
                <Label className='d-block' for='chk-ani7'>
                  <Input className='checkbox_animated' id='chk-ani7' type='checkbox' /> San Francisco<span className='d-block'>CA (252)</span>
                </Label>
                <Label className='d-block' for='chk-ani8'>
                  <Input className='checkbox_animated' id='chk-ani8' type='checkbox' /> Washington<span className='d-block'>DC (226)</span>
                </Label>
                <Label className='d-block' for='chk-ani9'>
                  <Input className='checkbox_animated' id='chk-ani9' type='checkbox' /> Seattle<span className='d-block'>WA (242)</span>
                </Label>
                <Label className='d-block mb-0' for='chk-ani10'>
                  <Input className='checkbox_animated' id='chk-ani10' type='checkbox' /> Chicago<span className='d-block'>IL (187)</span>
                </Label>
              </div>
            </CardBody>
            <Btn attrBtn={{ className: 'btn d-block w-100 text-center', color: 'primary', type: 'button' }}>All Locations</Btn>
          </Collapse>
        </Card>
      </Col>
    </Fragment>
  );
};

export default Location;
