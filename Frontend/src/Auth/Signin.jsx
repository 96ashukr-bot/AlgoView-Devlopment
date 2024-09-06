import React, { Fragment, useState, useEffect, useContext } from "react";
import { Col, Container, Form, FormGroup, Input, Label, Row } from "reactstrap";
import { Btn, H4, P } from "../AbstractElements";
import { Link } from "react-router-dom";

import {
  EmailAddress,
  ForgotPassword,
  Password,
  RememberPassword,
  SignIn,
} from "../Constant";

import { useNavigate } from "react-router-dom";
import man from "../assets/images/dashboard/profile.png";
import logoWhite from "../assets/images/logo/Algotradelogo.png";
// import logoDark from "../assets/images/logo/logoDark.png"; // Assuming you have this image as well.

import CustomizerContext from "../_helper/Customizer";
import OtherWay from "./OtherWay";
import { ToastContainer, toast } from "react-toastify";

const Signin = ({ selected }) => {
  const [email, setEmail] = useState("test@gmail.com");
  const [password, setPassword] = useState("test123");
  const [togglePassword, setTogglePassword] = useState(false);
  const history = useNavigate();
  const { layoutURL } = useContext(CustomizerContext);

  const [value, setValue] = useState(localStorage.getItem("profileURL" || man));
  const [name, setName] = useState(localStorage.getItem("Name"));

  useEffect(() => {
    localStorage.setItem("profileURL", man);
    localStorage.setItem("Name", "Emay Walter");
  }, [value, name]);

  const loginAuth = async (e) => {
    e.preventDefault();
    setValue(man);
    setName("Emay Walter");
    if (email === "test@gmail.com" && password === "test123") {
      localStorage.setItem("login", JSON.stringify(true));
      history(`/dashboard/default/${layoutURL}`);
      toast.success("Successfully logged in!..");
    } else {
      toast.error("You entered the wrong password or username!..");
    }
  };

  return (
    <Fragment>
      <Container fluid={true} className="p-0 login-page">
        <Row>
          <Col xs="12">
            <div className="login-card">
            <div>
                  <Link className="logo" to={process.env.PUBLIC_URL}>
                    <img
                      className="img-fluids for-light"
                      src={logoWhite}
                      alt="loginpage"
                    />
                    {/* <img className="img-fluid for-dark" src={logoDark} alt="loginpage" /> */}
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
                      />
                      <div
                        className="show-hide"
                        onClick={() => setTogglePassword(!togglePassword)}
                      >
                        <span className={togglePassword ? "" : "show"}></span>
                      </div>
                    </div>
                  </FormGroup>
                  <div className="position-relative form-group mb-0">
                    <div className="checkbox">
                      <Input id="checkbox1" type="checkbox" />
                      <Label className="text-muted" for="checkbox1">
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
                      }}
                    >
                      {SignIn}
                    </Btn>
                  </div>
                  <OtherWay />
                </Form>
              </div>
            </div>
          </Col>
        </Row>
      </Container>
      <ToastContainer />
    </Fragment>
  );
};

export default Signin;
