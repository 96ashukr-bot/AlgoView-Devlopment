import React, { Fragment, useState, useContext } from 'react';
import { Link } from 'react-router-dom';
import { Col, Container, Form, FormGroup, Input, Label, Row } from 'reactstrap';
import { Btn, H4, P, Image } from '../../../AbstractElements';
import logoWhite from '../../../assets/images/logo/logo (1).png';
import logoDark from '../../../assets/images/logo/logo (1).png';
import { LogoContext } from '../../UiKits/Logo/LogoContext';
import { toast, ToastContainer } from 'react-toastify';
import { requestPasswordReset } from '../../../Services/Authentication';
import './Auths.css';

const ForgetPwd = ({ logoClassMain }) => {
  const { logo } = useContext(LogoContext);
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [emailError, setEmailError] = useState('');

  const handleEmailChange = (e) => {
    setEmail(e.target.value);
    if (e.target.value.trim()) setEmailError('');
  };

  const validateEmail = (email) => {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email) return 'Email is required.';
    if (!emailPattern.test(email)) return 'Format of email is incorrect';
    return '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const error = validateEmail(email);
    if (error) {
      setEmailError(error);
      return;
    }

    setLoading(true);

    try {
      await requestPasswordReset(email);
      toast.success('Reset password link sent successfully.');
      setEmail('');
    } catch (error) {
      toast.error(error.message || 'An error occurred. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

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
                      <Image attrImage={{ className: 'img-fluids for-light', src: logo || logoWhite, alt: 'Company Logo'}} />
                      <Image attrImage={{ className: 'img-fluids for-dark', src: logo || logoDark, alt: 'Company Logo'}} />
                    </Link>
                  </div>
                  <div className='login-main'>
                    <Form className='theme-form login-form' onSubmit={handleSubmit}>
                      <H4>Reset Your Password</H4>
                      <FormGroup>
                        <Label className='m-0 col-form-label'>Enter Your Email</Label>
                        <Input
                          className={`form-control ${emailError ? '' : ''}`}
                          value={email}
                          onChange={handleEmailChange}
                          placeholder='Enter Email'
                          style={{
                            marginBottom: '6px',
                            borderColor: emailError ? 'red' : '',
                          }}
                        />
                        {emailError && <div className="error-message">{emailError}</div>}
                      </FormGroup>
                      <FormGroup className='text-end'>
                        <Btn attrBtn={{ className: 'btn-block btn-clr', type: 'submit', disabled: loading }}>
                          {loading ? (
                            <div className="spinner-border spinner-border-sm" role="status">
                              <span className="visually-hidden">Loading...</span>
                            </div>
                          ) : (
                            'Send'
                          )}
                        </Btn>
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

export default ForgetPwd;
