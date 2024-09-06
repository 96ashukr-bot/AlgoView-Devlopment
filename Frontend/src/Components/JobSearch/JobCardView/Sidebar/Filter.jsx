import { Btn, H5 } from '../../../../AbstractElements';
import React, { Fragment, useState } from 'react';
import { Card, CardBody, CardHeader, Col, Collapse, Input, Label } from 'reactstrap';

const Filter = () => {
  const [isFilter, setIsFilter] = useState(true);
  return (
    <Fragment>
      <Col xl='12'>
        <Card>
          <CardHeader>
            <H5 attrH5={{ className: 'mb-0 p-0' }}>
              <Btn attrBtn={{ className: 'btn btn-link', color: 'transperant', onClick: () => setIsFilter(!isFilter) }}>Filter</Btn>
            </H5>
          </CardHeader>
          <Collapse isOpen={isFilter}>
            <CardBody className='filter-cards-view animate-chk'>
              <div className='job-filter mb-3'>
                <div className='faq-form'>
                  <Input className='form-control' type='text' placeholder='Search..' />
                  <i className='search-icon' data-feather='search'></i>
                </div>
              </div>
              <div className='job-filter'>
                <div className='faq-form'>
                  <Input className='form-control' type='text' placeholder='location..' />
                  <i className='search-icon' data-feather='map-pin'></i>
                </div>
              </div>
              <div className='checkbox-animated'>
                <Label className='d-block' for='chk-ani'>
                  <Input className='checkbox_animated' id='chk-ani' type='checkbox' /> Full-time (8688)
                </Label>
                <Label className='d-block' for='chk-ani1'>
                  <Input className='checkbox_animated' id='chk-ani1' type='checkbox' />
                  Contract (503)
                </Label>
                <Label className='d-block' for='chk-ani2'>
                  <Input className='checkbox_animated' id='chk-ani2' type='checkbox' />
                  Part-time (288)
                </Label>
                <Label className='d-block' for='chk-ani3'>
                  <Input className='checkbox_animated' id='chk-ani3' type='checkbox' />
                  Internship (236)
                </Label>
                <Label className='d-block' for='chk-ani4'>
                  <Input className='checkbox_animated' id='chk-ani4' type='checkbox' />
                  Temporary (146)
                </Label>
                <Label className='d-block' for='chk-ani5'>
                  <Input className='checkbox_animated' id='chk-ani5' type='checkbox' />
                  Commission (25)
                </Label>
              </div>
              <Btn attrBtn={{ className: 'btn text-center', color: 'primary', type: 'button' }}>Find jobs</Btn>
            </CardBody>
          </Collapse>
        </Card>
      </Col>
    </Fragment>
  );
};

export default Filter;
