import React, { Fragment, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Col, Container, Form, FormGroup, Input, Label, Row } from "reactstrap";
import { Btn, H4, H6, P, Image } from "../../../AbstractElements";
import logoWhite from "../../../assets/images/logo/Algotradelogo.png";
import { resetPassword } from "../../../Services/Authentication";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const PasswordResetPage = ({ logoClassMain }) => {
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [togglePassword, setTogglePassword] = useState(false);

  const { uid, token } = useParams();
  const navigate = useNavigate();

  const cleanUid = uid?.replace(":", "") || "";  
  const cleanToken = token?.replace(":", "") || ""; 

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      toast.error("Passwords do not match.");
      return;
    }
    try {
      await resetPassword(cleanUid, cleanToken, newPassword, confirmPassword);
      toast.success("Password has been updated successfully.");
      setNewPassword("");
      setConfirmPassword("");
      // setTimeout(() => {
      //   navigate("/login");
      // }, 3000); 
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
                      <H4>Create Your Password</H4>
                      <FormGroup className="position-relative">
                        <Label>New Password</Label>
                        <div className="position-relative">
                          <Input
                            className="form-control"
                            type={togglePassword ? "text" : "password"}
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            required
                            placeholder="Enter New Password"
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
                      </FormGroup>
                      <FormGroup>
                        <Label>Confirm Password</Label>
                        <Input
                          className="form-control"
                          type="password"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          required
                          placeholder="Enter Confirm Password"
                        />
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
