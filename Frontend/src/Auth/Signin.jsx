import React, { Fragment, useState, useEffect, useContext } from "react";
import { Col, Container, Form, FormGroup, Input, Label, Row } from "reactstrap";
import { Btn, H4, P, Image } from "../AbstractElements";
import { Link, useNavigate } from "react-router-dom";
import man from "../assets/images/dashboard/profile.png";
import logoWhite from "../assets/images/logo/logo (1).png";
import logoDark from "../assets/images/logo/logo (1).png";
import { LogoContext } from "../Components/UiKits/Logo/LogoContext";
import CustomizerContext from "../_helper/Customizer";
import OtherWay from "./OtherWay";
import './Auth.css';
import { ToastContainer, toast } from "react-toastify";
import { login } from "../Services/Authentication";
import VerifyOTP from "../Components/Pages/Auth/VerifyOTP";
import { Eye, EyeOff, } from 'react-feather';
import {
  EmailAddress, ForgotPassword, Password, RememberPassword, SignIn,
} from "../Constant";

const Signin = ({ selected }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [togglePassword, setTogglePassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const history = useNavigate();
  const { layoutURL } = useContext(CustomizerContext);
  const { logo } = useContext(LogoContext);

  const [value, setValue] = useState(localStorage.getItem("profileURL" || man));
  const [name, setName] = useState(localStorage.getItem("Name"));

  useEffect(() => {
    localStorage.setItem("profileURL", man);
    localStorage.setItem("Name", "Emay Walter");
  }, [value, name]);

  // When submitted is false, the Enter key triggers the loginAuth function.
  // When submitted is true, the Enter key triggers the verifyOtp API by programmatically submitting the VerifyOTP form.
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Enter") {
        if (submitted) {
          document.querySelector("form.theme-form.login-form").dispatchEvent(new Event("submit"));
        } else {
          loginAuth(e);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [email, password, submitted]);


  const validateEmail = (email) => {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
  };

  const validateForm = () => {
    if (!email) {
      toast.error("Email is required!");
      return false;
    }
    if (!validateEmail(email)) {
      toast.error("Invalid email format!");
      return false;
    }
    if (!password) {
      toast.error("Password is required");
      return false;
    }
    return true;
  };

  const loginAuth = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);

    try {
      const response = await login(email, password);
      const { message } = response;

      localStorage.setItem("login", JSON.stringify(true));

      if (message.includes("OTP sent to your email")) {
        setSubmitted(true);
        toast.success("OTP sent to your email. Please verify.");
      } else {
        history("/dashboard/algoviewtech/admin");
        toast.success("Login successful! Redirecting to Dashboard...");
      }
    } catch (error) {
      if (error.message.includes("email")) {
        toast.error("You Entered The Wrong Email!");
      } else if (error.message.includes("password")) {
        toast.error("You Entered The Wrong Password!");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Fragment>
      <Container fluid={true} className="p-0 login-page">
        <Row>
          <Col xs="12">
            {submitted ? (
              <VerifyOTP email={email} />
            ) : (
              <div className="login-card login-card-responsive">
                <div>
                  <Link className="logo" to={process.env}>
                    {/* <img
                      className="img-fluids for-light img-fluids-responsive"
                      src={logoWhite}
                      alt="loginpage"
                    /> */}
                    <Image attrImage={{ className: 'img-fluids for-light img-fluids-responsive', src: logo || logoWhite, alt: 'Company Logo' }} />
                    <Image attrImage={{ className: 'img-fluids for-dark img-fluids-responsive', src: logo || logoDark, alt: 'Company Logo' }} />
                  </Link>
                </div>
                <div className="login-main login-tab">
                  <Form className="theme-form">
                    <H4>
                      {selected === "simpleLogin"
                        ? ""
                        : "Sign In To Your Account"}
                    </H4>
                    <P>{"Enter your email & password to login"}</P>
                    <FormGroup>
                      <Label className="col-form-label">{EmailAddress}</Label>
                      <Input
                        className="form-control"
                        type="email"
                        onChange={(e) => setEmail(e.target.value)}
                        value={email}
                        placeholder="Enter Your Email"
                      />
                    </FormGroup>
                    <FormGroup className="position-relative">
                      <Label className="col-form-label">{Password}</Label>
                      <div className="position-relative">
                        <Input
                          className="form-control"
                          type={togglePassword ? "text" : "password"}
                          onChange={(e) => setPassword(e.target.value)}
                          value={password}
                          placeholder="Enter Your Password"
                        />
                        <div
                          className="position-absolute top-0 end-0 p-2"
                          style={{ cursor: "pointer", marginTop: '5px' }}
                          onClick={() => setTogglePassword(!togglePassword)}
                        >
                          {togglePassword ? <Eye /> : <EyeOff />}
                        </div>
                      </div>
                    </FormGroup>
                    <div className="position-relative form-group mb-0">
                      <div className="checkbox">
                        <Input id="checkbox1" type="checkbox" />
                        <Label className="text-muted" htmlFor="checkbox1">
                          {RememberPassword}
                        </Label>
                      </div>
                      <a
                        className="link"
                        href="pages/authentication/forget-pwd/:layout"
                      >
                        {ForgotPassword}
                      </a>
                      <Btn
                        attrBtn={{
                          className: "d-block w-100 mt-2 btn-clr",
                          onClick: (e) => loginAuth(e),
                          disabled: loading,
                        }}
                      >
                        {loading ? (
                          <div className="spinner-border spinner-border-sm" role="status">
                            <span className="visually-hidden">Loading...</span>
                          </div>
                        ) : (
                          SignIn
                        )}
                      </Btn>
                    </div>
                    <OtherWay />
                  </Form>
                </div>
              </div>
            )}
          </Col>
        </Row>
      </Container>
      <ToastContainer />
    </Fragment>
  );
};

export default Signin;