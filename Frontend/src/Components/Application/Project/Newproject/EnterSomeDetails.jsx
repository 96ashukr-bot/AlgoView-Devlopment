import React, { Fragment } from 'react';
import { Col, FormGroup, Label, Row } from 'reactstrap';
import { EnterSomeDetails } from '../../../../Constant';

const EnterSomeDetailsClass = ({ register, errors }) => {
  return (
    <Fragment>
      <Row>
        <Col>
          <FormGroup>
            <Label>{EnterSomeDetails}</Label>
            <textarea className='form-control' name='description' rows='3' {...register('description', { required: true })} />
            <span style={{ color: 'red' }}>{errors.description && 'Some Details is required'}</span>
          </FormGroup>
        </Col>
      </Row>
    </Fragment>
  );
};

export default EnterSomeDetailsClass;
