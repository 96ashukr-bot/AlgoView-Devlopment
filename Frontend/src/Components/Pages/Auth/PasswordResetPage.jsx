import React, { Fragment, useState, useContext } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Col, Container, Form, FormGroup, Input, Label, Row, Progress } from "reactstrap";
import { Btn, H4, P, Image } from "../../../AbstractElements";
import { Eye, EyeOff } from 'react-feather';
import logoWhite from "../../../assets/images/logo/logo (1).png";
import { LogoContext } from "../../UiKits/Logo/LogoContext";
import { resetPassword } from "../../../Services/Authentication";
import './Auths.css';
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const PasswordResetPage = ({ logoClassMain }) => {
  const { logo } = useContext(LogoContext);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [togglePassword, setTogglePassword] = useState(false);
  const [toggleConfirmPassword, setToggleConfirmPassword] = useState(false);
  const [newPasswordError, setNewPasswordError] = useState("");
  const [confirmPasswordError, setConfirmPasswordError] = useState("");
  const [passwordStrength, setPasswordStrength] = useState(0);

  const { uid, token } = useParams();
  const navigate = useNavigate();

  const cleanUid = uid?.replace(":", "") || "";
  const cleanToken = token?.replace(":", "") || "";

  const calculatePasswordStrength = (password) => {
    let strength = 0;
    if (password.length >= 8) strength += 20;
    if (/[A-Z]/.test(password)) strength += 20;
    if (/[a-z]/.test(password)) strength += 20;
    if (/\d/.test(password)) strength += 20;
    if (/[@#$%^&*!]/.test(password)) strength += 20;
    return strength;
  };

  const validateNewPassword = () => {
    let isValid = true;
    const passwordRegex = /^(?=.*[A-Z])(?=.*[!@#$%^&*])[A-Za-z\d!@#$%^&*]{10,}$/;
    const digitCount = (newPassword.match(/\d/g) || []).length;

    setNewPasswordError("");

    if (!newPassword) {
      setNewPasswordError("New password is required.");
      isValid = false;
    } else if (newPassword.length < 8) {
      setNewPasswordError("Password must be at least 8 characters.");
      isValid = false;
    } else if (!passwordRegex.test(newPassword)) {
      setNewPasswordError("Password must start with a first capital letter, contain a special character, 4 digits, with text.");
      isValid = false;
    } else if (digitCount < 4) {
      setNewPasswordError("Password must contain at least 4 digits.");
      isValid = false;
    }

    return isValid;
  };

  const validateConfirmPassword = () => {
    let isValid = true;
    setConfirmPasswordError("");

    if (!confirmPassword) {
      setConfirmPasswordError("Confirm password is required.");
      isValid = false;
    } else if (newPassword !== confirmPassword) {
      setConfirmPasswordError("Passwords do not match.");
      isValid = false;
    }

    return isValid;
  };

  const handlePasswordChange = (e) => {
    const password = e.target.value;
    setNewPassword(password);
    setPasswordStrength(calculatePasswordStrength(password));
    if (password.trim()) setNewPasswordError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!validateNewPassword() || !validateConfirmPassword()) {
      return;
    }

    try {
      await resetPassword(cleanUid, cleanToken, newPassword, confirmPassword);
      toast.success("Password has been updated successfully.");
      setNewPassword("");
      setConfirmPassword("");
      setTimeout(() => {
        navigate("/login");
      }, 3000);
    } catch (err) {
      setError(err.message || "Failed to reset password.");
      toast.error(err.message || "Failed to reset password.");
    }
  };

  return (
    <Fragment>
      <section>
        <Container className="p-0 login-page" fluid={true}>
          <Row className="m-0">
            <Col className="p-0">
              <div className="login-card login-card-responsive">
                <div>
                  <div>
                    <Link
                      className={`logo ${logoClassMain ? logoClassMain : ""}`}
                      to={process.env.PUBLIC_URL}
                    >
                      {/* <Image
                        attrImage={{
                          className: "img-fluids img-fluids-responsive for-light",
                          src: logoWhite,
                          alt: "loginpage",
                        }}
                      /> */}
                      <Image attrImage={{ className: 'img-fluids for-light img-fluids-responsive', src: logo || logoWhite, alt: 'Company Logo' }} />

                    </Link>
                  </div>
                  <div className="login-main">
                    <Form
                      className="theme-form login-form"
                      onSubmit={handleSubmit}
                    >
                      <H4>Change Your Password</H4>

                      {/* Password Requirements */}
                      <div style={{ marginBottom: '20px' }}>
                        <ul>
                          <li>Must be at least 8 characters long.</li>
                          <li>Should contain at least one uppercase letter (A-Z).</li>
                          <li>Should contain at least one lowercase letter (a-z).</li>
                          <li>Must include at least one number (0-9).</li>
                          <li>Must include at least one special character (e.g., @, #, $, %).</li>
                        </ul>
                      </div>

                      {/* New Password Field */}
                      <FormGroup className="position-relative">
                        <Label>New Password</Label>
                        <div className="position-relative">
                          <Input
                            className={`form-control ${newPasswordError ? '' : ''}`}
                            type={togglePassword ? "text" : "password"}
                            value={newPassword}
                            onChange={handlePasswordChange}
                            placeholder="Enter New Password"
                            style={{
                              borderColor: newPasswordError ? 'red' : '',
                            }}
                          />
                          <div
                            className="password-toggle"
                            onClick={() => setTogglePassword(!togglePassword)}
                            style={{ position: "absolute", top: "11px", right: "10px", cursor: "pointer" }}
                          >
                            {togglePassword ? <Eye size={25} /> : <EyeOff size={25} />}
                          </div>
                        </div>
                        {newPasswordError && <p style={{ color: "red" }}>{newPasswordError}</p>}

                        {/* Conditionally render the Password Strength Progress */}
                        {newPassword && (
                          <>
                            <Progress
                              value={passwordStrength}
                              color={
                                passwordStrength < 40
                                  ? "danger"
                                  : passwordStrength < 80
                                    ? "warning"
                                    : "success"
                              }
                              className="mt-2"
                            />
                            <small>
                              {passwordStrength < 40
                                ? 'Weak'
                                : passwordStrength < 80
                                  ? 'Medium'
                                  : 'Strong'}
                            </small>
                          </>
                        )}
                      </FormGroup>

                      {/* Confirm Password Field */}
                      <FormGroup className="position-relative">
                        <Label>Confirm Password</Label>
                        <div className="position-relative">
                          <Input
                            className={`form-control ${confirmPasswordError ? '' : ''}`}
                            type={toggleConfirmPassword ? "text" : "password"}
                            value={confirmPassword}
                            onChange={(e) => {
                              setConfirmPassword(e.target.value);
                              if (e.target.value.trim()) setConfirmPasswordError('');
                            }}
                            placeholder="Enter Confirm Password"
                            style={{
                              borderColor: confirmPasswordError ? 'red' : '',
                            }}
                          />
                          <div
                            className="password-toggle"
                            onClick={() => setToggleConfirmPassword(!toggleConfirmPassword)}
                            style={{ position: "absolute", top: "10px", right: "10px", cursor: "pointer" }}
                          >
                            {/* {toggleConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />} */}
                          </div>
                        </div>
                        {confirmPasswordError && <p style={{ color: "red" }}>{confirmPasswordError}</p>}
                      </FormGroup>

                      {error && <p style={{ color: "red" }}>{error}</p>}
                      <FormGroup>
                        <Btn
                          attrBtn={{
                            className: "btn d-block w-100 btn-clr",
                            type: "submit",
                          }}
                        >
                          Done
                        </Btn>
                      </FormGroup>
                      <P>
                        Already have a password? <a href="/login">Sign in</a>
                      </P>
                    </Form>
                  </div>
                </div>
              </div>
            </Col>
          </Row>
        </Container>
      </section>
      <ToastContainer position="top-right" autoClose={5000} />
    </Fragment>
  );
};

export default PasswordResetPage;
