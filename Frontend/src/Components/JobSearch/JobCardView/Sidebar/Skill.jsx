import { Btn, H5 } from '../../../../AbstractElements';
import React, { Fragment, useState } from 'react';
import { Card, CardHeader, CardBody, Col, Input, Label, Collapse } from 'reactstrap';

const SkillClass = () => {
  const [isFilter, setIsFilter] = useState(true);
  return (
    <Fragment>
      <Col xl='12'>
        <Card>
          <CardHeader>
            <H5 attrH5={{ className: 'mb-0 p-0' }}>
              <Btn attrBtn={{ className: 'btn btn-link', color: 'transperant', onClick: () => setIsFilter(!isFilter) }}>Specific skills</Btn>
            </H5>
          </CardHeader>
          <Collapse isOpen={isFilter}>
            <CardBody className='animate-chk'>
              <Label className='d-block' for='chk-ani21'>
                <Input className='checkbox_animated' id='chk-ani21' type='checkbox' /> HTML,scss & sass
              </Label>
              <Label className='d-block' for='chk-ani22'>
                <Input className='checkbox_animated' id='chk-ani22' type='checkbox' /> Javascript
              </Label>
              <Label className='d-block' for='chk-ani23'>
                <Input className='checkbox_animated' id='chk-ani23' type='checkbox' /> Node.js
              </Label>
              <Label className='d-block' for='chk-ani24'>
                <Input className='checkbox_animated' id='chk-ani24' type='checkbox' /> Gulp & Pug
              </Label>
              <Label className='d-block mb-0' for='chk-ani25'>
                <Input className='checkbox_animated' id='chk-ani25' type='checkbox' /> Angular.js
              </Label>
            </CardBody>
            <Btn attrBtn={{ className: 'btn d-block w-100 text-center', color: 'primary', type: 'button' }}>All Skills</Btn>
          </Collapse>
        </Card>
      </Col>
    </Fragment>
  );
};

export default SkillClass;
