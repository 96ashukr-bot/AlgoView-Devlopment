import React, { Fragment, useState, useEffect, useContext } from "react";
import { Col, Container, Form, FormGroup, Input, Label, Row } from "reactstrap";
import { Btn, H4, P } from "../AbstractElements";
import { Link } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import man from "../assets/images/dashboard/profile.png";
import logoWhite from "../assets/images/logo/Algotradelogo.png";
import CustomizerContext from "../_helper/Customizer";
import OtherWay from "./OtherWay";
import { ToastContainer, toast } from "react-toastify";
import { login } from "../Services/Authentication";

import {
  EmailAddress,
  ForgotPassword,
  Password,
  RememberPassword,
  SignIn,
} from "../Constant";

const Signin = ({ selected }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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

    try {
      // Call the login API and get the response
      const response = await login(email, password);
      
      localStorage.setItem("login", JSON.stringify(true));
      history(`/dashboard/default/${layoutURL}`);
      toast.success("Login successful!"); 
    } catch (error) {
      if (error.message.includes("email")) {
        toast.error("You Entered The Wrong Email!");
      } else if (error.message.includes("password")) {
        toast.error("You Entered The Wrong Password!");
      } else {
        toast.error("You Entered The Wrong Email or Password!");
      }
    }
  };

  return (
    <Fragment>
      <Container fluid={true} className="p-0 login-page">
        <Row>
          <Col xs="12">
            <div className="login-card">
              <div>
                <Link className="logo" to={process.env}>
                  <img
                    className="img-fluids for-light"
                    src={logoWhite}
                    alt="loginpage"
                  />
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
