import React, { Fragment } from 'react';
import { H3, H4, P, Image } from '../../../../AbstractElements';
import { InvoiceHash, IssuedJan, PaymentDue } from '../../../../Constant';
import { Col, Media, Row } from 'reactstrap';
import logo1 from '../../../../assets/images/other-images/logo-login.png';

const InvoiceHeader = () => {
  return (
    <Fragment>
      <Row className='invo-header'>
        <Col sm='6'>
          <Media>
            <div className='media-left'>
              <Image attrImage={{ className: 'media-object img-60', src: logo1, alt: '' }} />
            </div>
            <Media body className='m-l-20 text-right'>
              <H4 attrH4={{ className: 'media-heading f-w-600' }}>Cuba</H4>
              <P>
                hello@Cuba.in
                <br />
                <span className='digits'>{'289-335-6503'}</span>
              </P>
            </Media>
          </Media>
        </Col>
        <Col sm='6'>
          <div className='text-md-end text-xs-center'>
            <H3>
              {InvoiceHash}
              <span className='digits counter'>1069</span>
            </H3>
            <P>
              {IssuedJan}
              <span className='digits'>27, 2022</span>
              <br />
              {PaymentDue} <span className='digits'> 27, 2022</span>
            </P>
          </div>
        </Col>
      </Row>
      <hr />
    </Fragment>
  );
};
export default InvoiceHeader;
