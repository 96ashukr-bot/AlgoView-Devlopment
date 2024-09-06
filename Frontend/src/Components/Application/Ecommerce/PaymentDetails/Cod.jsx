import React, { Fragment } from 'react';
import { Btn } from '../../../../AbstractElements';
import { COD, Submit } from '../../../../Constant';
import { Card, CardBody, Col, FormGroup, Input, Row } from 'reactstrap';
import HeaderCard from '../../../Common/Component/HeaderCard';

const CashonDelivery = () => {
  return (
    <Fragment>
      <Col lg='6' xxl='4' className='box-col-6'>
        <Card>
          <HeaderCard title={COD} />
          <CardBody>
            <Row className='theme-form'>
              <FormGroup className='mb-3 col-6 p-r-0'>
                <Input className='form-control' type='text' placeholder='First Name' />
              </FormGroup>
              <FormGroup className='col-6'>
                <Input className='form-control' type='text' placeholder='Last name' />
              </FormGroup>
              <FormGroup className='mb-3 col-6 p-r-0'>
                <Input className='form-control' type='text' placeholder='Pincode' />
              </FormGroup>
              <FormGroup className='col-6'>
                <Input className='form-control' type='number' placeholder='Enter mobile number' />
              </FormGroup>
              <FormGroup className='mb-3 col-6 p-r-0'>
                <Input className='form-control' type='text' placeholder='State' />
              </FormGroup>
              <FormGroup className='col-6'>
                <Input className='form-control' type='text' placeholder='City' />
              </FormGroup>
              <FormGroup className='mb-3 col-12'>
                <textarea className='form-control' rows='3' placeholder='Address'></textarea>
              </FormGroup>
              <div className='col-12'>
                <Btn attrBtn={{ color: 'primary', className: 'btn btn-primary ' }}>{Submit}</Btn>
              </div>
            </Row>
          </CardBody>
        </Card>
      </Col>
    </Fragment>
  );
};
export default CashonDelivery;
