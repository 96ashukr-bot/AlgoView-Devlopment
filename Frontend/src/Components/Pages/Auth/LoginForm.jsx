import React, { Fragment, useContext, useState } from 'react';
import { Btn, H4, P, Image } from '../../../AbstractElements';
import { Form, FormGroup, Input, Label } from 'reactstrap';
import { Link } from 'react-router-dom';
// import { Facebook, Linkedin, Twitter } from 'react-feather';
import { LogoContext } from '../../UiKits/Logo/LogoContext';

const LoginForm = ({ logoClassMain }) => {
  console.log(logoClassMain,'logoClassMain')
  const { logo } = useContext(LogoContext);
  const [togglePassword, setTogglePassword] = useState(false);
  return (
    <Fragment>
      <div className='login-card'>
        <div>
          <div>
            <Link className={`logo ${logoClassMain ? logoClassMain : ''}`} to={process.env.PUBLIC_URL}>
              {logo && (
                <>
                  <Image attrImage={{ className: 'img-fluids for-light', src: logo, alt: 'Company Logo' }} />
                  <Image attrImage={{ className: 'img-fluids for-dark', src: logo, alt: 'Company Logo' }} />
                </>
              )}
            </Link>
          </div>

          <div className='login-main'>
            <Form className='theme-form login-form'>
              <H4>Sign in to account</H4>
              <P>Enter your email & password to login</P>
              <FormGroup>
                <Label className='col-form-label m-0'>Email Address</Label>
                <Input className='form-control' type='email' required placeholder='Test@gmail.com' />
              </FormGroup>
              <FormGroup className='position-relative'>
                <Label className='col-form-label m-0'>Password</Label>
                <div className='position-relative'>
                  <Input className='form-control' type={togglePassword ? 'text' : 'password'} name='login[password]' required placeholder='*********' />
                  <div className='show-hide' onClick={() => setTogglePassword(!togglePassword)}>
                    <span className={togglePassword ? '' : 'show'}></span>
                  </div>
                </div>
              </FormGroup>
              <FormGroup className='position-relative'>
                <div className='checkbox'>
                  <Input id='checkbox1' type='checkbox' />
                  <Label className='text-muted' for='checkbox1'>
                    Remember password
                  </Label>
                </div>
                <Link className='link' to={`/pages/authentication/forget-pwd/:layout`}>
                  Forgot password?
                </Link>
              </FormGroup>
              <FormGroup>
                <Btn attrBtn={{ className: 'd-block w-100 mt-2 btn-clr', type: 'submit' }}>Sign in</Btn>
              </FormGroup>
              <P attrPara={{ className: 'text-center mb-0 ' }}>
                Don't have account?
                <Link className='ms-2' to={`/pages/authentication/register-simple/:layout`}>
                  Create Account
                </Link>
              </P>
            </Form>
          </div>
        </div>
      </div>
    </Fragment>
  );
};

export default LoginForm;
