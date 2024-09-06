import React, { Fragment } from 'react';
import { Col, Card, CardHeader, CardBody, Form, FormGroup, Label, Input } from 'reactstrap';
import { Btn, H5, H6 } from '../../../../AbstractElements';
import { Password, Username, InlineForm, InlineFormWithLabel, InlineFormWithoutLabel, Login } from '../../../../Constant';

const InlineFormClass = () => {
  return (
    <Fragment>
      <Col xl='12'>
        <Card>
          <CardHeader>
            <H5>{InlineForm}</H5>
            <span>
              {'Use'}
              <code>{'.form-inline'}</code>
              {'class in the form to style with inline fields.'}
            </span>
          </CardHeader>
          <CardBody>
            <H6>{InlineFormWithLabel}</H6>
            <Form className='row theme-form mt-3'>
              <div className='col-lg-4 mb-3 d-flex'>
                <Label className='col-form-label pe-2'>{Username}</Label>
                <Input className='form-control' type='text' name='inputUsername' placeholder='Username' autoComplete='off' />
              </div>
              <div className='col-lg-4 mb-3 d-flex'>
                <Label className='col-form-label pe-2'>{Password}</Label>
                <Input className='form-control' type='password' name='inputPassword' placeholder='Password' autoComplete='off' />
              </div>
              <div className='col-lg-4 mb-3 d-flex'>
                <Btn attrBtn={{ color: 'primary' }}>{Login}</Btn>
              </div>
            </Form>
            <H6>{InlineFormWithoutLabel}</H6>
            <Form className='row row-cols-sm-3 theme-form mt-3 billing-form'>
              <FormGroup className='d-flex'>
                <Input className='form-control' type='text' name='inputUnlabelUsername' placeholder='Username' autoComplete='off' />
              </FormGroup>
              <FormGroup className='d-flex'>
                <Input className='form-control' type='password' name='inputPassword' placeholder='Password' autoComplete='off' />
              </FormGroup>
              <FormGroup className='d-flex'>
                <Btn attrBtn={{ color: 'secondary' }}>{Login}</Btn>
              </FormGroup>
            </Form>
          </CardBody>
        </Card>
      </Col>
    </Fragment>
  );
};

export default InlineFormClass;
