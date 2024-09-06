import React, { Fragment } from 'react';
import { Col, Card, CardHeader, CardBody, Form, Label, Input, InputGroup, InputGroupText, Row } from 'reactstrap';
import { CustomStyles, Username } from '../../../../Constant';
import { useForm } from 'react-hook-form';
import { Btn, H5 } from '../../../../AbstractElements';

const CustomStylesClass = () => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm();

  const onSubmit = (data) => {
    if (data !== '') {
      alert('You submitted the form and stuff!');
    } else {
      errors.showMessages();
    }
  };
  return (
    <Fragment>
      <Card>
        <CardHeader>
          <H5>{CustomStyles}</H5>
          <span>
            For custom Bootstrap form validation messages, you’ll need to add the <code className='text-danger'>novalidate</code> boolean attribute to your <code className='text-danger'>&lt;form&gt;</code>. This disables the browser default feedback tooltips, but still provides access to the form validation APIs in JavaScript. Try to submit the form below; our JavaScript will intercept the submit
            button and relay feedback to you.
          </span>
          <span>
            When attempting to submit, you’ll see the <code className='text-danger'>:invalid </code> and <code className='text-danger'>:valid </code> styles applied to your form controls.
          </span>
        </CardHeader>
        <CardBody>
          <Form className='needs-validation' noValidate='' onSubmit={handleSubmit(onSubmit)}>
            <Row>
              <Col md='4 mb-3'>
                <Label className='form-label' for='validationCustom01'>
                  First name
                </Label>
                <input className='form-control' id='validationCustom01' type='text' placeholder='Mark' name='fName' {...register('fName', { required: true })} />
                <span className='d-block'>{errors.fName && 'First name is required'}</span>
                <div className='valid-feedback'>Looks good!</div>
              </Col>
              <Col md='4 mb-3'>
                <Label className='form-label' for='validationCustom02'>
                  Last name
                </Label>
                <input className='form-control' id='validationCustom02' type='text' placeholder='Otto' name='lName' {...register('lName', { required: true })} />
                <span className='d-block'>{errors.lName && 'Last name is required'}</span>
                <div className='valid-feedback'>Looks good!</div>
              </Col>
              <Col md='4 mb-3'>
                <Label htmlFor='validationCustomUsername'>{Username}</Label>
                <InputGroup>
                  <InputGroupText>{'@'}</InputGroupText>
                  <input className='form-control' name='userName' type='text' placeholder='Username' {...register('userName', { required: true })} />
                  <span className='d-block w-100'>{errors.userName && 'User name is required'}</span>
                </InputGroup>
              </Col>
            </Row>
            <Row>
              <Col md='6 mb-3'>
                <Label className='form-label' for='validationCustom03'>
                  City
                </Label>
                <Input className='form-control' id='validationCustom03' type='text' placeholder='City' required='' {...register('city', { required: true })} />
                <span className='d-block'>{errors.city && 'Please provide a valid city.'}</span>
                <div className='invalid-feedback'>Please provide a valid city.</div>
              </Col>
              <Col md='3 mb-3'>
                <Label className='form-label' for='validationCustom04'>
                  State
                </Label>
                <input className='form-control' id='validationCustom04' name='state' type='text' placeholder='State' {...register('state', { required: true })} />
                <span className='d-block'>{errors.state && 'Please provide a valid state.'}</span>
                <div className='invalid-feedback'>{'Please provide a valid state.'}</div>
              </Col>
              <Col md='3' className='mb-3'>
                <Label className='form-label' for='validationCustom05'>
                  Zip
                </Label>
                <Input className='form-control' id='validationCustom05' type='text' placeholder='Zip' name='zip' {...register('zip', { required: true })} />
                <span className='d-block'>{errors.zip && 'Please provide a valid zip.'}</span>
                <div className='invalid-feedback'>Please provide a valid zip.</div>
              </Col>
            </Row>
            <div>
              <div className='form-check'>
                <div className='checkbox p-0'>
                  <Input className='form-check-input' id='invalidCheck' type='checkbox' />
                  <Label className='form-check-label' htmlFor='invalidCheck'>
                    {'Agree to terms and conditions'}
                  </Label>
                </div>
                <div className='invalid-feedback'>{'You must agree before submitting.'}</div>
              </div>
            </div>
            <Btn attrBtn={{ color: 'primary' }}>{'Submit form'}</Btn>
          </Form>
        </CardBody>
      </Card>
    </Fragment>
  );
};

export default CustomStylesClass;
