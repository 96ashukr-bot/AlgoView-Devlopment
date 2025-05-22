import React, { Fragment, useState, useEffect, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Col, Container, Form, FormGroup, Input, Label, Row } from 'reactstrap';
import { Btn, H4, P, Image } from '../../../AbstractElements';
import logoWhite from '../../../assets/images/logo/logo (1).png';
import logoDark from '../../../assets/images/logo/logo (1).png';
import { LogoContext } from '../../UiKits/Logo/LogoContext';
import { verifyOtp, resendOtp } from '../../../Services/Authentication';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const VerifyOTP = ({ email }) => {
  const { logo } = useContext(LogoContext);
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [timer, setTimer] = useState(120);
  const [isResendDisabled, setIsResendDisabled] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    let countdown;
    if (timer > 0) {
      countdown = setInterval(() => {
        setTimer((prevTimer) => prevTimer - 1);
      }, 1000);
    } else {
      setIsResendDisabled(false);
      clearInterval(countdown);
    }

    return () => clearInterval(countdown);
  }, [timer]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      console.log("Key pressed:", e.key);
      if (e.key === "Enter") {
        console.log("Enter key detected.");

        if (otp.length === 6) {
          e.preventDefault();
          console.log("OTP is valid. Triggering handleSubmit...");
          handleSubmit(e);
        } else {
          console.log("Invalid OTP length:", otp.length);
        }
      }
    };

    console.log("Adding keydown event listener.");
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      console.log("Removing keydown event listener.");
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [otp, email]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);

    if (otp.length !== 6) {
      setError('Please enter a valid 6-digit OTP');
      setLoading(false);
      return;
    }

    try {
      const response = await verifyOtp(email, otp);

      if (response.message === "Please change your password as this is a one-time temporary password.") {
        toast.success('Account verified! Please change your password.');
        navigate('/pages/authentication/create-pwd/:layout');
      } else if (response.message === "login successfully") {
        if (response.ekyc_status === true) {
          toast.success('Login successful! Redirecting to dashboard.');
          navigate('/dashboard/algoviewtech/user');
        }
        else {
          navigate('/algoview/kyc-update');
        }

      } else {
        setError('Unexpected response from server.');
      }
    } catch (err) {
      toast.error(err.message || 'OTP verification failed');
      setError(err.message || 'OTP verification failed');
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (e) => {
    const value = e.target.value;
    setOtp(value);

    if (value.length === 6) {
      setError('');
    } else if (value.length > 6) {
      setError('OTP cannot exceed 6 digits.');
    } else {
      setError('');
    }
  };

  const handleResendOtp = async () => {
    setLoading(true);
    try {
      const response = await resendOtp(email);
      if (response.success) {
        toast.success('A new OTP has been resent to your registered email.');
        setTimer(120);
        setIsResendDisabled(true);
      } else {
        toast.error('Failed to resend OTP.');
      }
    } catch (error) {
      toast.error(error.message || 'Failed to resend OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs < 10 ? '0' : ''}${secs}`;
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
                      <Image attrImage={{ className: 'img-fluids for-light', src: logo || logoWhite, alt: 'Company Logo' }} />
                      <Image attrImage={{ className: 'img-fluids for-dark', src: logo || logoDark, alt: 'Company Logo' }} />
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
                              className={`form-control text-center otp-text ${error ? '' : ''}`}
                              type='text'
                              placeholder='000000'
                              maxLength='6'
                              value={otp}
                              onChange={handleOtpChange}
                              style={{
                                borderColor: error ? 'red' : '',
                              }}
                            />
                            {error && (
                              <P attrPara={{ className: "error-clr", style: { color: "red" } }}>
                                {error}
                              </P>
                            )}
                          </Col>
                        </Row>
                      </FormGroup>
                      <FormGroup className='text-end'>
                        <Btn attrBtn={{
                          className: 'd-block  btn-clr', type: 'submit', disabled: loading,
                          onClick: (e) => handleSubmit(e),
                        }}>
                          {loading ? (
                            <div className="spinner-border spinner-border-sm" role="status">
                              <span className="visually-hidden">Loading...</span>
                            </div>
                          ) : (
                            'Verify'
                          )}
                        </Btn>
                      </FormGroup>
                      <FormGroup className='mb-4 mt-4'>
                        <span className='reset-password-link'>
                          {isResendDisabled ? (
                            <>
                              Resend OTP available in <strong>{formatTime(timer)}</strong>
                            </>
                          ) : (
                            <>
                              Didn't receive OTP?{' '}
                              <a
                                className='btn-link text-danger'
                                href='#resend-otp'
                                onClick={handleResendOtp}
                              >
                                Resend
                              </a>
                            </>
                          )}
                        </span>
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
