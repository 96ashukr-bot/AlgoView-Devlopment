import React, { Fragment, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Col, Container, Form, FormGroup, Input, Label, Row } from 'reactstrap';
import { Btn, H4, P, Image } from '../../../AbstractElements';
import logoWhite from '../../../assets/images/logo/Algologo.png';
import { changePassword } from '../../../Services/Authentication';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const CreatePwd = ({ logoClassMain }) => {
  const [toggleOldPassword, setToggleOldPassword] = useState(false);
  const [toggleNewPassword, setToggleNewPassword] = useState(false);
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');
  const [errors, setErrors] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  const navigate = useNavigate(); 

  const getAuthToken = () => {
    return localStorage.getItem('authToken'); 
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();

    let valid = true;
    const newErrors = {
      oldPassword: '',
      newPassword: '',
      confirmPassword: '',
    };

    if (oldPassword.length < 8) {
      newErrors.oldPassword = 'Password must be at least 8 characters long.';
      valid = false;
    }
    if (newPassword.length < 8) {
      newErrors.newPassword = 'Must contain at least 8 characters.';
      valid = false;
    }
    if (newPassword !== confirmPassword) {
      newErrors.confirmPassword = 'New passwords do not match.';
      valid = false;
    }

    setErrors(newErrors);

    if (!valid) {
      return;
    }

    try {
      const response = await changePassword(oldPassword, newPassword, confirmPassword);
      // setMessage(response.message || "Password successfully changed, please login with the new password.");
      
      toast.success('New Password Created Successfully!');

      setTimeout(() => {
        navigate('/dashboard/default/Admin');
      }, 2000);
      
    } catch (error) {
      setMessage(error.message || "Failed to change password.");
      toast.error(error.message || "Failed to change password.");
    }
  };

  return (
    <Fragment>
      <section>
        <Container fluid={true} className='p-0 login-page'>
          <Row className='m-0'>
            <Col xl='12 p-0'>
              <div className='login-card'>
                <div>
                  <div>
                    <Link className={`logo ${logoClassMain ? logoClassMain : ''}`} to={process.env.PUBLIC_URL}>
                      <Image attrImage={{ className: 'img-fluids for-light', src: logoWhite, alt: 'loginpage' }} />
                    </Link>
                  </div>
                  <div className='login-main'>
                    <Form className='theme-form login-form' onSubmit={handlePasswordChange}>
                      <H4>Create Your Password</H4>

                      {/* Old Password Field */}
                      <FormGroup className='position-relative'>
                        <Label className='m-0 col-form-label'>Old Password</Label>
                        <div className='position-relative'>
                          <Input
                            className={`form-control ${errors.oldPassword ? 'is-invalid' : ''}`}
                            type={toggleOldPassword ? 'text' : 'password'}
                            name='old_password'
                            required
                            placeholder='Enter Old Password'
                            value={oldPassword}
                            onChange={(e) => setOldPassword(e.target.value)}
                          />
                          <div className='show-hide' onClick={() => setToggleOldPassword(!toggleOldPassword)}>
                            <span className={`toggle-icon ${toggleOldPassword ? 'show' : 'hide'}`}></span>
                          </div>
                        </div>
                        {errors.oldPassword && <small className='text-danger'>{errors.oldPassword}</small>}
                      </FormGroup>

                      {/* New Password Field */}
                      <FormGroup className='position-relative'>
                        <Label className='m-0 col-form-label'>New Password</Label>
                        <div className='position-relative'>
                          <Input
                            className={`form-control ${errors.newPassword ? 'is-invalid' : ''}`}
                            type={toggleNewPassword ? 'text' : 'password'}
                            name='new_password'
                            required
                            placeholder='Enter New Password'
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                          />
                          <div className='show-hide' onClick={() => setToggleNewPassword(!toggleNewPassword)}>
                            <span className={`toggle-icon ${toggleNewPassword ? 'show' : 'hide'}`}></span>
                          </div>
                        </div>
                        {errors.newPassword && <small className='text-danger'>{errors.newPassword}</small>}
                      </FormGroup>

                      {/* Confirm New Password Field */}
                      <FormGroup>
                        <Label className='m-0 col-form-label'>Confirm New Password</Label>
                        <Input
                          className={`form-control ${errors.confirmPassword ? 'is-invalid' : ''}`}
                          type='password'
                          name='confirm_password'
                          required
                          placeholder='Enter Confirm New Password'
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                        />
                        {errors.confirmPassword && <small className='text-danger'>{errors.confirmPassword}</small>}
                      </FormGroup>

                      {/* Submit Button */}
                      <FormGroup>
                        <Btn attrBtn={{ className: 'd-block w-100 btn-clr', color: 'primary', type: 'submit' }}>
                          Done
                        </Btn>
                      </FormGroup>

                      {/* Message for feedback */}
                      {message && <P attrPara={{ className: 'text-muted' }}>{message}</P>}

                      {/* Account creation link */}
                      <P attrPara={{ className: 'mb-0' }}>
                        Don't have an account?
                        <a className='ps-2' href='/pages/authentication/register-simple/:layout'>
                          Create Account
                        </a>
                      </P>
                    </Form>
                  </div>
                </div>
              </div>
            </Col>
          </Row>
        </Container>

        {/* Toast Container for displaying notifications */}
        <ToastContainer />
      </section>
    </Fragment>
  );
};

export default CreatePwd;
