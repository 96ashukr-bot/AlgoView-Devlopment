import React, { Fragment, useState, useContext } from 'react';
import { Form, FormGroup, Input, Label, Row, Col } from 'reactstrap';
import { Btn, H4, P, H6, Image } from '../../../AbstractElements';
import { Link, useNavigate } from 'react-router-dom';
import logoWhite from '../../../assets/images/logo/logo (1).png';
import logoDark from '../../../assets/images/logo/logo (1).png';
import { LogoContext } from '../../UiKits/Logo/LogoContext';
import { signupUser } from '../../../Services/Authentication';
import { toast, ToastContainer } from 'react-toastify';
import './Auths.css';
import 'react-toastify/dist/ReactToastify.css';

const RegisterFrom = ({ logoClassMain }) => {
  const { logo } = useContext(LogoContext);

  const [formValues, setFormValues] = useState({
    firstName: '',
    lastName: '',
    phoneNumber: '',
    email: '',
  });

  const [formErrors, setFormErrors] = useState({
    firstName: '',
    lastName: '',
    phoneNumber: '',
    email: '',
  });

  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const validate = () => {
    let errors = {};
    let valid = true;
    const phoneRegex = /^[0-9]{10}$/;

    if (!formValues.firstName.trim()) {
      errors.firstName = 'First name is required';
      valid = false;
    }

    if (!formValues.lastName.trim()) {
      errors.lastName = 'Last name is required';
      valid = false;
    }

    if (!formValues.phoneNumber || !phoneRegex.test(formValues.phoneNumber)) {
      errors.phoneNumber = 'Phone Number must be exactly 10 digits';
      valid = false;
    }

    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!formValues.email.trim() || !emailPattern.test(formValues.email)) {
      errors.email = 'Valid email address is required';
      valid = false;
    }

    setFormErrors(errors);
    return valid;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;

    let newErrors = { ...formErrors };

    switch (name) {
      case 'firstName':
        if (value.trim()) newErrors.firstName = '';
        break;
      case 'lastName':
        if (value.trim()) newErrors.lastName = '';
        break;
      case 'phoneNumber':
        if (value.length >= 10) newErrors.phoneNumber = '';
        break;
      case 'email':
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (emailPattern.test(value)) newErrors.email = '';
        break;
      default:
        break;
    }

    setFormValues({
      ...formValues,
      [name]: value,
    });

    setFormErrors(newErrors);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    setLoading(true);

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
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      }
    } catch (error) {
      if (error.response && error.response.data) {
        const responseData = error.response.data;

        // Check if the error contains a phone number conflict
        if (Array.isArray(responseData.phoneNumber) && responseData.phoneNumber.includes("Phone number already exists.")) {
          toast.error('Phone number already exists. Please use a different phone number.', {
            position: toast.POSITION.TOP_RIGHT,
            autoClose: 3000,
          });
        }
        // Check if the error contains an email conflict
        else if (Array.isArray(responseData.email) && responseData.email.some(msg => msg.includes("user with this email already exists."))) {
          toast.error('Email already exists. Please use a different email.', {
            position: toast.POSITION.TOP_RIGHT,
            autoClose: 3000,
          });
        }
        // Generic error message
        else {
          toast.error('An error occurred. Please try again later.', {
            position: toast.POSITION.TOP_RIGHT,
            autoClose: 3000,
          });
        }
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Fragment>
      <div className='login-card login-card-responsive'>
        <div>
          <Link className={`logo ${logoClassMain ? logoClassMain : ''}`} to={process.env.PUBLIC_URL}>
            <Image attrImage={{ className: 'img-fluids for-light img-fluids-responsive', src: logo || logoWhite, alt: 'Company Logo' }} />
            <Image attrImage={{ className: 'img-fluids for-dark img-fluids-responsive ', src: logo || logoDark, alt: 'Company Logo' }} />
          </Link>
          <div className='login-main'>
            <Form className='theme-form login-form' onSubmit={handleSubmit}>
              <H4>Create your account</H4>
              <P>Enter your personal details to create an account</P>

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
                      placeholder='First Name'
                      style={{
                        marginBottom: '6px',
                        borderColor: formErrors.firstName ? 'red' : '',
                      }}
                    />
                    {formErrors.firstName && (
                      <span style={{ color: 'red' }}>{formErrors.firstName}</span>
                    )}
                  </Col>
                  <Col xs='6'>
                    <Input
                      className='form-control'
                      type='text'
                      name='lastName'
                      value={formValues.lastName}
                      onChange={handleInputChange}
                      placeholder='Last Name'
                      style={{
                        marginBottom: '6px',
                        borderColor: formErrors.lastName ? 'red' : '',
                      }}
                    />
                    {formErrors.lastName && (
                      <span style={{ color: 'red' }}>{formErrors.lastName}</span>
                    )}
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
                  placeholder='Enter Your Number'
                  style={{
                    marginBottom: '6px',
                    borderColor: formErrors.phoneNumber ? 'red' : '',
                  }}
                />
                {formErrors.phoneNumber && (
                  <span style={{ color: 'red' }}>{formErrors.phoneNumber}</span>
                )}
              </FormGroup>

              <FormGroup>
                <Label className='col-form-label m-0 pt-0'>Email Address <span className='text-danger'>*</span></Label>
                <Input
                  className='form-control'
                  name='email'
                  value={formValues.email}
                  onChange={handleInputChange}
                  placeholder='Enter Your Email'
                  style={{
                    marginBottom: '6px',
                    borderColor: formErrors.email ? 'red' : '',
                  }}
                />
                {formErrors.email && (
                  <span style={{ color: 'red' }}>{formErrors.email}</span>
                )}
              </FormGroup>

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
        <ToastContainer />
      </div>
    </Fragment>
  );
};

export default RegisterFrom;
