import React, { Fragment, useState } from 'react';
import { Link } from 'react-router-dom';
import { Col, Container, Form, FormGroup, Input, Label, Row } from 'reactstrap';
import { Btn, H4, H6, P, Image } from '../../../AbstractElements';
import logoWhite from '../../../assets/images/logo/Algotradelogo.png';
import logoDark from '../../../assets/images/logo/logo_dark.png';

const ForgetPwd = ({ logoClassMain }) => {
  const [togglePassword, setTogglePassword] = useState(false);
  const [mobilePrefix, setMobilePrefix] = useState('+91');
  const [mobileNumber, setMobileNumber] = useState('');
  const [otp, setOtp] = useState(['00', '00', '00']);
  const [newPassword, setNewPassword] = useState('');
  const [retypePassword, setRetypePassword] = useState('');

  const handleMobilePrefixChange = (e) => setMobilePrefix(e.target.value);
  const handleMobileNumberChange = (e) => setMobileNumber(e.target.value);
  const handleOtpChange = (index, value) => {
    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);
  };
  const handleNewPasswordChange = (e) => setNewPassword(e.target.value);
  const handleRetypePasswordChange = (e) => setRetypePassword(e.target.value);

  return (
    <Fragment>
      <section>
        <Container className='p-0 login-page' fluid={true}>
          <Row className='m-0'>
            <Col className='p-0'>
              <div className='login-card'>
                <div>
                  <div>
                    <Link className={`logo ${logoClassMain ? logoClassMain : ''}`} to={process.env.PUBLIC_URL}>
                      <Image attrImage={{ className: 'img-fluids for-light', src: logoWhite, alt: 'loginpage' }} />
                      <Image attrImage={{ className: 'img-fluid for-dark', src: logoDark, alt: 'loginpage' }} />
                    </Link>
                  </div>
                  <div className='login-main'>
                    <Form className='theme-form login-form'>
                      <H4>Reset Your Password</H4>
                      <FormGroup>
                        <Label className='m-0 col-form-label'>Enter Your Mobile Number</Label>
                        <Row>
                          <Col xs='4' sm='3'>
                            <Input
                              className='form-control'
                              type='text'
                              value={mobilePrefix}
                              onChange={handleMobilePrefixChange}
                            />
                          </Col>
                          <Col xs='8' sm='9'>
                            <Input
                              className='form-control'
                              type='text'
                              value={mobileNumber}
                              onChange={handleMobileNumberChange}
                            />
                          </Col>
                        </Row>
                      </FormGroup>
                      <FormGroup className='text-end'>
                        <Btn attrBtn={{ className: 'btn-block btn-clr', type: 'submit' }}>Send</Btn>
                      </FormGroup>
                      <FormGroup className='mb-4 mt-4'>
                        <span className='reset-password-link'>
                          If you don't receive OTP?  
                          <a className='btn-link text-danger' href=''>
                            Resend
                          </a>
                        </span>
                      </FormGroup>
                      {/* <FormGroup>
                        <Label>Enter OTP</Label>
                        <Row>
                          {otp.map((value, index) => (
                            <Col key={index}>
                              <Input
                                className='form-control text-center opt-text'
                                type='text'
                                value={value}
                                maxlength='2'
                                onChange={(e) => handleOtpChange(index, e.target.value)}
                              />
                            </Col>
                          ))}
                        </Row>
                      </FormGroup> */}
                      {/* <H6 attrH6={{ className: 'mt-4' }}>Create Your Password</H6> */}
                      {/* <FormGroup className='position-relative'>
                        <Label className='col-form-label m-0'>New Password</Label>
                        <div className='position-relative'>
                          <Input
                            className='form-control'
                            type={togglePassword ? 'text' : 'password'}
                            name='login[password]'
                            required
                            placeholder='*********'
                            value={newPassword}
                            onChange={handleNewPasswordChange}
                          />
                          <div className='show-hide' onClick={() => setTogglePassword(!togglePassword)}>
                            <span className={togglePassword ? '' : 'show'}></span>
                          </div>
                        </div>
                      </FormGroup> */}
                      {/* <FormGroup>
                        <Label className='col-form-label m-0'>Retype Password</Label>
                        <Input
                          className='form-control'
                          type='password'
                          name='login[password]'
                          required
                          placeholder='*********'
                          value={retypePassword}
                          onChange={handleRetypePasswordChange}
                        />
                      </FormGroup> */}
                      {/* <FormGroup>
                        <div className='checkbox'>
                          <Input id='checkbox1' type='checkbox' />
                          <Label className='text-muted' for='checkbox1'>
                            Remember password
                          </Label>
                        </div>
                      </FormGroup> */}
                      {/* <FormGroup>
                        <Btn attrBtn={{ className: 'btn d-block w-100 btn-clr', type: 'submit' }}>Done</Btn>
                      </FormGroup> */}
                      <P attrPara={{ className: 'text-start' }}>
                        Already have a password?
                        <a className='ms-2' href='/login'>
                          Sign in
                        </a>
                      </P>
                    </Form>
                  </div>
                </div>
              </div>
            </Col>
          </Row>
        </Container>
      </section>
    </Fragment>
  );
};

export default ForgetPwd;
