import React, { Fragment, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Col, Container, Form, FormGroup, Input, Label, Row } from "reactstrap";
import { Btn, H4, P, Image } from "../../../AbstractElements";
import logoWhite from "../../../assets/images/logo/Algotradelogo.png";
import { resetPassword } from "../../../Services/Authentication";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const PasswordResetPage = ({ logoClassMain }) => {
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [togglePassword, setTogglePassword] = useState(false);
  const [newPasswordError, setNewPasswordError] = useState("");
  const [confirmPasswordError, setConfirmPasswordError] = useState("");

  const { uid, token } = useParams();
  const navigate = useNavigate();

  const cleanUid = uid?.replace(":", "") || "";  
  const cleanToken = token?.replace(":", "") || ""; 

  const validate = () => {
    let isValid = true;

    setNewPasswordError("");
    setConfirmPasswordError("");

    if (!newPassword) {
      setNewPasswordError("New password is required.");
      isValid = false;
    } else if (newPassword.length < 8) {
      setNewPasswordError("Password must be at least 8 characters.");
      isValid = false;
    }

    if (!confirmPassword) {
      setConfirmPasswordError("Confirm password is required.");
      isValid = false;
    } else if (newPassword !== confirmPassword) {
      setConfirmPasswordError("Passwords do not match.");
      isValid = false;
    }

    return isValid;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!validate()) {
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
              <div className="login-card">
                <div>
                  <div>
                    <Link
                      className={`logo ${logoClassMain ? logoClassMain : ""}`}
                      to={process.env.PUBLIC_URL}
                    >
                      <Image
                        attrImage={{
                          className: "img-fluids for-light",
                          src: logoWhite,
                          alt: "loginpage",
                        }}
                      />
                    </Link>
                  </div>
                  <div className="login-main">
                    <Form
                      className="theme-form login-form"
                      onSubmit={handleSubmit}
                    >
                      <H4>Change Your Password</H4>
                      <FormGroup className="position-relative">
                        <Label>New Password</Label>
                        <div className="position-relative">
                          <Input
                            className={`form-control ${newPasswordError ? '' : ''}`}
                            type={togglePassword ? "text" : "password"}
                            value={newPassword}
                            onChange={(e) => {
                              setNewPassword(e.target.value);
                              if (e.target.value.trim()) setNewPasswordError('');
                            }}
                            placeholder="Enter New Password"
                            style={{
                              borderColor: newPasswordError ? 'red' : '',
                            }}
                          />
                          <div
                            className="show-hide"
                            onClick={() => setTogglePassword(!togglePassword)}
                          >
                            <span
                              className={togglePassword ? "" : "show"}
                            ></span>
                          </div>
                        </div>
                        {newPasswordError && <p style={{ color: "red" }}>{newPasswordError}</p>}
                      </FormGroup>
                      <FormGroup>
                        <Label>Confirm Password</Label>
                        <Input
                          className={`form-control ${confirmPasswordError ? '' : ''}`}
                          type="password"
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
      <ToastContainer position="top-right" autoClose={3000} hideProgressBar />
    </Fragment>
  );
};

export default PasswordResetPage;
