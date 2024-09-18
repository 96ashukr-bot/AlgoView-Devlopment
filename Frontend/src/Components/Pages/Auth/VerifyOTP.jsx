import React, { Fragment, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Col, Container, Form, FormGroup, Input, Label, Row } from 'reactstrap';
import { Btn, H4, P, Image } from '../../../AbstractElements';
import logoWhite from '../../../assets/images/logo/Algologo.png';
import logoDark from '../../../assets/images/logo/logo_dark.png';
import { verifyOtp } from '../../../Services/Authentication';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const VerifyOTP = ({ email }) => {  
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      if (otp.length < 6) {
        setError('Please enter a valid OTP');
        return;
      }

      const response = await verifyOtp(email, otp);
      
      toast.success('Account verified successfully');
      
      console.log('OTP verified successfully:', response);
      navigate('/dashboard/default/Admin'); 
    } catch (err) {
      toast.error('OTP IS INVALID');
      
      setError(err.message || 'OTP verification failed');
    }
  };

  return (
    <Fragment>
      <section>
        <Container className='p-0 login-page' fluid>
          <Row className='m-0'>
            <Col className='p-0'>
              <div className='login-card'>
                <div>
                  <div>
                    <Link className={`logo`} to={process.env.PUBLIC_URL}>
                      <Image attrImage={{ className: 'img-fluids for-light', src: logoWhite, alt: 'Logo' }} />
                      <Image attrImage={{ className: 'img-fluid for-dark', src: logoDark, alt: 'Logo' }} />
                    </Link>
                  </div>
                  <div className='login-main'>
                    <Form className='theme-form login-form' onSubmit={handleSubmit}>
                      <H4>Verify Your OTP</H4>
                      <FormGroup>
                        <Label for='otp' className='m-0'>Enter OTP</Label>
                        <Row>
                          <Col>
                            <Input
                              id='otp'
                              className='form-control text-center otp-text'
                              type='text'
                              placeholder='000000'
                              maxLength='6'
                              value={otp}
                              onChange={(e) => setOtp(e.target.value)}
                              required
                            />
                          </Col>
                        </Row>
                        {error && <P style={{ color: 'red' }}>{error}</P>}
                      </FormGroup>
                      <FormGroup className='text-end'>
                        <Btn attrBtn={{ className: 'btn-block btn-clr', color: 'primary', type: 'submit' }}>Verify</Btn>
                      </FormGroup>
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
      <ToastContainer />
    </Fragment>
  );
};

export default VerifyOTP;
