import React, { Fragment, useState } from 'react';
// import { Facebook, Linkedin, Twitter } from 'react-feather';
import { Form, FormGroup, Input, Label, Row, Col } from 'reactstrap';
import { Btn, H4, P, H6, Image } from '../../../AbstractElements';
import { Link } from 'react-router-dom';
import logoWhite from '../../../assets/images/logo/Algotradelogo.png';
import logoDark from '../../../assets/images/logo/logo_dark.png';

const RegisterFrom = ({ logoClassMain }) => {
  const [togglePassword, setTogglePassword] = useState(false);
  return (
    <Fragment>
      <div className='login-card'>
        <div>
          <div>
            <Link className={`logo ${logoClassMain ? logoClassMain : ''}`} to={process.env.PUBLIC_URL}>
              <Image attrImage={{ className: 'img-fluids for-light', src: logoWhite, alt: 'looginpage' }} />
              <Image attrImage={{ className: 'img-fluid for-dark', src: logoDark, alt: 'looginpage' }} />
            </Link>
          </div>
          <div className='login-main'>
            <Form className='theme-form login-form'>
              <H4>Create your account</H4>
              <P>Enter your personal details to create account</P>
              <FormGroup>
                <Label className='col-form-label m-0 pt-0'>Your Name</Label>
                <Row className='g-2'>
                  <Col xs='6'>
                    <Input className='form-control' type='text' required='' placeholder='First Name' />
                  </Col>
                  <Col xs='6'>
                    <Input className='form-control' type='text' required='' placeholder='Last Name' />
                  </Col>
                </Row>
              </FormGroup>
              <FormGroup>
                <Label className='col-form-label m-0 pt-0'>Phone Number</Label>
                <Input className='form-control' type='number' required='' placeholder='Enter Your Number' />
              </FormGroup>
              <FormGroup>
                <Label className='col-form-label m-0 pt-0'>Email Address</Label>
                <Input className='form-control' type='email' required='' placeholder='Enter Your Email' />
              </FormGroup>
              <FormGroup className='position-relative'>
                <Label className='col-form-label m-0 pt-0'>Password</Label>
                <div className='position-relative'>
                  <Input className='form-control' type={togglePassword ? 'text' : 'password'} name='login[password]' required placeholder='*********' />
                  <div className='show-hide' onClick={() => setTogglePassword(!togglePassword)}>
                    <span className={togglePassword ? '' : 'show'}></span>
                  </div>
                </div>
              </FormGroup>
              <FormGroup className='m-0'>
                <div className='checkbox'>
                  <Input id='checkbox1' type='checkbox' />
                  <Label className='text-muted' for='checkbox1'>
                    Agree with <span>Privacy Policy</span>
                  </Label>
                </div>
              </FormGroup>
              <FormGroup>
                <Btn attrBtn={{ className: 'd-block w-100 btn-clr', type: 'submit' }}>Create Account</Btn>
              </FormGroup>

              <P attrPara={{ className: 'mb-0 text-start' }}>
                Already have an account?
                <Link className='ms-2' to={`/login`}>
                  Sign in
                </Link>
              </P>
            </Form>
          </div>
        </div>
      </div>
    </Fragment>
  );
};

export default RegisterFrom;
