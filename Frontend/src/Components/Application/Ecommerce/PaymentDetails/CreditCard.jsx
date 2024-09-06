import { Image } from '../../../../AbstractElements';
import { CreditCard } from '../../../../Constant';
import card from '../../../../assets/images/ecommerce/card.png';
import { Card, CardBody, Col, Form, FormGroup, Input, Row } from 'reactstrap';
import React, { Fragment } from 'react';
import HeaderCard from '../../../Common/Component/HeaderCard';

const CreditCards = () => {
  return (
    <Fragment>
      <Col xxl='8' className='box-col-12'>
        <Card className='height-equal credit-form card'>
          <HeaderCard title={CreditCard} />
          <CardBody>
            <Row>
              <Col md='7'>
                <Form className='theme-form mega-form'>
                  <FormGroup className='mb-3'>
                    <Input className='form-control' type='text' placeholder='Card number' />
                  </FormGroup>
                  <FormGroup className='mb-3'>
                    <Input className='form-control' type='text' placeholder='First Name' />
                  </FormGroup>
                  <FormGroup className='mb-3'>
                    <Input className='form-control' type='date' />
                  </FormGroup>
                  <FormGroup className='mb-3'>
                    <Input className='form-control' type='text' placeholder='Name on card' />
                  </FormGroup>
                  <div>
                    <select className='form-select form-control' size='1'>
                      <option>Select Type</option>
                      <option>Master</option>
                      <option>Visa</option>
                    </select>
                  </div>
                </Form>
              </Col>
              <Col md='5' className='text-center'>
                <Image
                  attrImage={{
                    className: 'img-fluid',
                    src: `${card}`,
                    alt: '',
                  }}
                />
              </Col>
            </Row>
          </CardBody>
        </Card>
      </Col>
    </Fragment>
  );
};
export default CreditCards;
