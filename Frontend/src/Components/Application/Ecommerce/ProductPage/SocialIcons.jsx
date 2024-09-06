import React, { Fragment } from 'react';
import { H6, LI, UL } from '../../../../AbstractElements';
import { Col, Form, Row } from 'reactstrap';

const SocialIcons = () => {
  return (
    <Fragment>
      <div className='pro-group'>
        <Row>
          <Col md='4'>
            <H6 attrH6={{ className: 'product-title' }}>{'share it'}</H6>
          </Col>
          <Col md='8'>
            <div className='product-icon'>
              <UL attrUL={{ className: 'simple-list border-0 d-flex flex-row product-social' }}>
                <LI attrLI={{ className: 'd-inline-block border-0' }}>
                  <a href='https://www.facebook.com/'>
                    <i className='fa fa-facebook'></i>
                  </a>
                </LI>
                <LI attrLI={{ className: 'd-inline-block border-0' }}>
                  <a href='https://accounts.google.com/'>
                    <i className='fa fa-google-plus'></i>
                  </a>
                </LI>
                <LI attrLI={{ className: 'd-inline-block border-0' }}>
                  <a href='https://twitter.com/'>
                    <i className='fa fa-twitter'></i>
                  </a>
                </LI>
                <LI attrLI={{ className: 'd-inline-block border-0' }}>
                  <a href='https://www.instagram.com/'>
                    <i className='fa fa-instagram'></i>
                  </a>
                </LI>
                <LI attrLI={{ className: 'd-inline-block border-0' }}>
                  <a href='https://dashboard.rss.com/auth/sign-in/'>
                    <i className='fa fa-rss'></i>
                  </a>
                </LI>
              </UL>
              <Form className='d-inline-block f-right'></Form>
            </div>
          </Col>
        </Row>
      </div>
    </Fragment>
  );
};
export default SocialIcons;
