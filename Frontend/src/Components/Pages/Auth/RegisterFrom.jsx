import React, { Fragment, useState } from 'react';
import { Form, FormGroup, Input, Label, Row, Col } from 'reactstrap';
import { Btn, H4, P, H6, Image } from '../../../AbstractElements';
import { Link, useNavigate } from 'react-router-dom';
import logoWhite from '../../../assets/images/logo/Algotradelogo.png';
import logoDark from '../../../assets/images/logo/logo_dark.png';
import { signupUser } from '../../../Services/Authentication';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const RegisterFrom = ({ logoClassMain }) => {
  const [formValues, setFormValues] = useState({
    firstName: '',
    lastName: '',
    phoneNumber: '',
    email: '',
  });

  const [errorMessage, setErrorMessage] = useState('');
  const [loading, setLoading] = useState(false); // Add loading state
  const navigate = useNavigate();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormValues({
      ...formValues,
      [name]: value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); // Set loading to true when form submission starts

    try {
      const response = await signupUser(formValues);
      if (response.status === 201) {
        setFormValues({
          firstName: '',
          lastName: '',
          phoneNumber: '',
          email: '',
        }); 
        toast.success('Your account is created successfully!', {
          position: toast.POSITION.TOP_RIGHT,
          autoClose: 3000,
        });
        // Redirect after successful signup if needed
        // navigate('/login'); 
      }
    } catch (error) {
      setErrorMessage('Error creating account. Please try again.');
      toast.error('Error creating account. Please try again.', {
        position: toast.POSITION.TOP_RIGHT,
        autoClose: 3000,
      });
    } finally {
      setLoading(false); 
    }
  };

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
            <Form className='theme-form login-form' onSubmit={handleSubmit}>
              <H4>Create your account</H4>
              <P>Enter your personal details to create account</P>

              <FormGroup>
                <Label className='col-form-label m-0 pt-0'>Your Name <span className='text-danger'>*</span></Label>
                <Row className='g-2'>
                  <Col xs='6'>
                    <Input
                      className='form-control'
                      type='text'
                      name='firstName'
                      value={formValues.firstName}
                      onChange={handleInputChange}
                      required
                      placeholder='First Name'
                    />
                  </Col>
                  <Col xs='6'>
                    <Input
                      className='form-control'
                      type='text'
                      name='lastName'
                      value={formValues.lastName}
                      onChange={handleInputChange}
                      required
                      placeholder='Last Name'
                    />
                  </Col>
                </Row>
              </FormGroup>

              <FormGroup>
                <Label className='col-form-label m-0 pt-0'>Phone Number <span className='text-danger'>*</span></Label>
                <Input
                  className='form-control'
                  type='number'
                  name='phoneNumber'
                  value={formValues.phoneNumber}
                  onChange={handleInputChange}
                  required
                  placeholder='Enter Your Number'
                />
              </FormGroup>

              <FormGroup>
                <Label className='col-form-label m-0 pt-0'>Email Address <span className='text-danger'>*</span></Label>
                <Input
                  className='form-control'
                  type='email'
                  name='email'
                  value={formValues.email}
                  onChange={handleInputChange}
                  required
                  placeholder='Enter Your Email'
                />
              </FormGroup>
              <FormGroup className='m-0'>
                <div className='checkbox'>
                  <Input id='checkbox1' type='checkbox' required />
                  <Label className='text-muted' for='checkbox1'>
                    Agree with <span>Privacy Policy</span>
                  </Label>
                </div>
              </FormGroup>

              {errorMessage && <P className="text-danger">{errorMessage}</P>}

              <FormGroup>
                <Btn attrBtn={{ className: 'd-block w-100 btn-clr', type: 'submit', disabled: loading }}>
                  {loading ? (
                    <div className="spinner-border spinner-border-sm" role="status">
                      <span className="visually-hidden">Loading...</span>
                    </div>
                  ) : (
                    'Create Account'
                  )}
                </Btn>
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
      
      <ToastContainer />
    </Fragment>
  );
};

export default RegisterFrom;
