import React, { Fragment, useState } from 'react';
import DatePicker from 'react-datepicker';
import { Col, InputGroup, Label, Row } from 'reactstrap';

const DateTime2 = () => {
  const [startDate, setStartDate] = useState(new Date());
  const handleChange = (date) => {
    setStartDate(date);
  };
  return (
    <Fragment>
      <Row className='mb-3 g-3'>
        <Label className='col-sm-3 col-form-label text-end'>No Icon (input field only)</Label>
        <Col xl='5' sm='7' lg='8'>
          <DatePicker className='form-control datetimepicker-input digits' selected={startDate} showTimeSelect onChange={handleChange} dateFormat='MMMM d, yyyy h:mm aa' />
        </Col>
      </Row>
      <Row className='mb-3 g-3'>
        <Label className='col-sm-3 col-form-label text-end'>Enabled/Disabled Dates</Label>
        <Col xl='5' sm='7' lg='8'>
          <InputGroup className='date flex-nowrap' id='dt-enab-disab-date' data-target-input='nearest'>
            <DatePicker className='form-control datetimepicker-input digits' selected={startDate} showTimeSelect onChange={(date) => setStartDate(date)} dateFormat='MMMM d, yyyy h:mm aa' />
            <div className='input-group-text' data-target='#dt-enab-disab-date' data-toggle='datetimepicker'>
              <i className='fa fa-calendar'></i>
            </div>
          </InputGroup>
        </Col>
      </Row>
      <Row className='mb-3 g-3'>
        <Label className='col-sm-3 col-form-label text-end'>View Mode</Label>
        <Col xl='5' sm='7' lg='8'>
          <InputGroup className='date flex-nowrap' id='dt-view' data-target-input='nearest'>
            <DatePicker className='form-control datetimepicker-input digits' selected={startDate} showTimeSelect onChange={(date) => setStartDate(date)} dateFormat='MMMM d, yyyy h:mm aa' />
            <div className='input-group-text' data-target='#dt-view' data-toggle='datetimepicker'>
              <i className='fa fa-calendar'></i>
            </div>
          </InputGroup>
        </Col>
      </Row>
      <div className='mb-3 row g-3 mb-0'>
        <Label className='col-sm-3 col-form-label text-end'>Disabled Days of the Week</Label>
        <Col xl='5' sm='7' lg='8'>
          <InputGroup className='date flex-nowrap' id='dt-disab-days' data-target-input='nearest'>
            <DatePicker className='form-control datetimepicker-input digits' selected={startDate} showTimeSelect onChange={(date) => setStartDate(date)} dateFormat='MMMM d, yyyy h:mm aa' />
            <div className='input-group-text' data-target='#dt-disab-days' data-toggle='datetimepicker'>
              <i className='fa fa-calendar'></i>
            </div>
          </InputGroup>
        </Col>
      </div>
    </Fragment>
  );
};
export default DateTime2;
