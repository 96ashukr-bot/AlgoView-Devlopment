import React, { Fragment, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Col, Container, Form, FormGroup, Input, Label, Row, Progress, Spinner } from 'reactstrap';
import { Btn, H4, P, Image } from '../../../AbstractElements';
import logoWhite from '../../../assets/images/logo/logo (1).png';
import { changePassword } from '../../../Services/Authentication';
import './Auths.css';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { Eye, EyeOff } from 'react-feather';

const CreatePwd = ({ logoClassMain }) => {
  const [toggleOldPassword, setToggleOldPassword] = useState(false);
  const [toggleNewPassword, setToggleNewPassword] = useState(false);
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  const [passwordStrength, setPasswordStrength] = useState(0);
  const navigate = useNavigate();

  const evaluatePasswordStrength = (password) => {
    let strength = 0;

    if (password.length >= 8) strength += 1;
    if (/[A-Z]/.test(password)) strength += 1;
    if (/[a-z]/.test(password)) strength += 1;
    if (/\d/.test(password)) strength += 1;
    if (/\W/.test(password)) strength += 1;

    return strength;
  };

  const validateOldPassword = () => {
    if (!oldPassword) return 'Old Password is required.';
    if (oldPassword.length < 8) return 'Password must be at least 8 characters long.';
    return '';
  };

  const validateNewPassword = () => {
    if (!newPassword) return 'New Password is required.';
    if (newPassword.length < 8) return 'Must contain at least 8 characters.';

    const passwordRegex = /^[A-Z](?=.*\W)(?=.*\d.*\d.*\d.*\d).{7,}$/;

    if (!passwordRegex.test(newPassword)) {
      return 'Password must start with a capital letter, contain a special character, and include exactly 4 digits.';
    }
    return '';
  };

  const validateConfirmPassword = () => {
    if (!confirmPassword) return 'Confirm New Password is required.';
    if (newPassword !== confirmPassword) return 'New passwords do not match.';
    return '';
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();

    const newErrors = {
      oldPassword: validateOldPassword(),
      newPassword: validateNewPassword(),
      confirmPassword: validateConfirmPassword(),
    };

    setErrors(newErrors);
    const isValid = Object.values(newErrors).every((error) => error === '');

    if (!isValid) return;

    setIsLoading(true); 

    try {
      const response = await changePassword(oldPassword, newPassword, confirmPassword);

      if (response.ekyc_status === true) {
        toast.success('New Password Created Successfully!');
        setTimeout(() => {
          navigate('/dashboard/algoviewtech/user');
        }, 2000);
      } else {
        setTimeout(() => {
          navigate('/algoview/kyc-update');
        }, 2000);
      }
    } catch (error) {
      setMessage(error.message || 'Failed to change password.');
      toast.error(error.message || 'Failed to change password.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewPasswordChange = (e) => {
    const password = e.target.value;
    setNewPassword(password);

    const strength = evaluatePasswordStrength(password);
    setPasswordStrength(strength);

    if (errors.newPassword) {
      setErrors((prevErrors) => ({
        ...prevErrors,
        newPassword: validateNewPassword(),
      }));
    }
  };

  const getProgressBarColor = (strength) => {
    switch (strength) {
      case 1:
      case 2:
        return 'danger';
      case 3:
      case 4:
        return 'warning';
      case 5:
        return 'success';
      default:
        return 'danger';
    }
  };

  return (
    <Fragment>
      <section>
        <Container fluid={true} className="p-0 login-page">
          <Row className="m-0">
            <Col xl="12 p-0">
              <div className="login-card login-card-responsive">
                <div>
                  <div>
                    <Link className={`logo ${logoClassMain ? logoClassMain : ''}`} to={process.env.PUBLIC_URL}>
                      <Image attrImage={{ className: 'img-fluids img-fluids-responsive for-light', src: logoWhite, alt: 'loginpage' }} />
                    </Link>
                  </div>
                  <div className="login-main">
                    <Form className="theme-form login-form" onSubmit={handlePasswordChange}>
                      <H4>Create Your Password</H4>

                      {/* Old Password Field */}
                      <FormGroup className="position-relative">
                        <Label className="m-0 col-form-label">Old Password</Label>
                        <Input
                          className={`form-control ${errors.oldPassword ? '' : ''}`}
                          style={{ borderColor: errors.oldPassword ? 'red' : '' }}
                          type={toggleOldPassword ? 'text' : 'password'}
                          name="old_password"
                          placeholder="Enter Old Password"
                          value={oldPassword}
                          onChange={(e) => setOldPassword(e.target.value)}
                        />
                        <div className="show-hides" onClick={() => setToggleOldPassword(!toggleOldPassword)}>
                          {toggleOldPassword ? <Eye /> : <EyeOff />} 
                        </div>
                        {errors.oldPassword && <small className="text-danger">{errors.oldPassword}</small>}
                      </FormGroup>

                      {/* Password Requirements */}
                      <div className="password-requirements mb-3">
                        <ul className="text-muted">
                          <li>Must be at least 8 characters long.</li>
                          <li>Should contain at least one uppercase letter (A-Z).</li>
                          <li>Should contain at least one lowercase letter (a-z).</li>
                          <li>Must include at least one number (0-9).</li>
                          <li>Must include at least one special character (e.g., @, #, $, %).</li>
                        </ul>
                      </div>

                      {/* New Password Field with Strength Progress Bar */}
                      <FormGroup className="position-relative">
                        <Label className="m-0 col-form-label">New Password</Label>
                        <Input
                          className={`form-control ${errors.newPassword ? '' : ''}`}
                          style={{ borderColor: errors.newPassword ? 'red' : '' }}
                          type={toggleNewPassword ? 'text' : 'password'}
                          name="new_password"
                          placeholder="Enter New Password"
                          value={newPassword}
                          onChange={handleNewPasswordChange}
                        />
                        <div className="show-hides" onClick={() => setToggleNewPassword(!toggleNewPassword)}>
                          {toggleNewPassword ? <Eye /> : <EyeOff />} 
                        </div>
                        {errors.newPassword && <small className="text-danger">{errors.newPassword}</small>}

                        {/* Password Strength Progress Bar */}
                        {newPassword && (
                          <Fragment>
                            <Progress
                              value={(passwordStrength / 5) * 100}
                              color={getProgressBarColor(passwordStrength)}
                              className="mt-2"
                            />
                            <small> {passwordStrength >= 5 ? 'Strong' : passwordStrength >= 3 ? 'Medium' : 'Weak'}</small>
                          </Fragment>
                        )}
                      </FormGroup>

                      {/* Confirm New Password Field */}
                      <FormGroup>
                        <Label className="m-0 col-form-label">Confirm New Password</Label>
                        <Input
                          className={`form-control ${errors.confirmPassword ? '' : ''}`}
                          style={{ borderColor: errors.confirmPassword ? 'red' : '' }}
                          type="password"
                          name="confirm_password"
                          placeholder="Enter Confirm New Password"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                        />
                        {errors.confirmPassword && <small className="text-danger">{errors.confirmPassword}</small>}
                      </FormGroup>

                      {/* Submit Button */}
                      <FormGroup>
                        <Btn attrBtn={{ className: 'd-block w-100 btn-clr', color: 'primary', type: 'submit', disabled: isLoading }}>
                          {isLoading ? <Spinner size="sm" /> : 'Done'}
                        </Btn>
                      </FormGroup>
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

export default CreatePwd;
