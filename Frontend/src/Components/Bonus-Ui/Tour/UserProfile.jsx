import React, { Fragment, useEffect, useState } from 'react';
import { Col, Card, CardHeader, Row } from 'reactstrap';
import { H6, Image } from '../../../AbstractElements';
import { BOD, ContactUs, ContactUsNumber, DDMMYY, Designer, Email, Follower, Following, LocationDetails, MarekjecnoMailId, MarkJecno, Location } from '../../../Constant';

const UserProfile = () => {
  const [url, setUrl] = useState('');

  // Load URL from local storage on component mount
  useEffect(() => {
    const savedUrl = localStorage.getItem('profileImageUrl');
    if (savedUrl) {
      setUrl(savedUrl);
    }
  }, []);

  const readUrl = (event) => {
    if (event.target.files.length === 0) return;
    const file = event.target.files[0];
    const mimeType = file.type;

    if (!mimeType.match(/image\/*/)) {
      return;
    }

    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const imageUrl = reader.result;
      setUrl(imageUrl);
      // Save URL to local storage
      localStorage.setItem('profileImageUrl', imageUrl);
    };
  };

  return (
    <Fragment>
      <Col sm='12'>
        <Card className='hovercard text-center'>
          <CardHeader className='cardheader'></CardHeader>
          <div className='user-image'>
            <div className='avatar'>
              <Image attrImage={{ className: 'step1', alt: '', src: `${url ? url : require('../../../assets/images/user/7.jpg')}` }} />
            </div>
            <div className='icon-wrapper step2' data-intro='Change Profile image here'>
              <i className='icofont icofont-pencil-alt-5'>
                <input className='upload' type='file' onChange={readUrl} />
              </i>
            </div>
          </div>
          <div className='info'>
            <Row className='step3' data-intro='This is the your details'>
              <Col sm='6' lg='4' className='order-sm-1 order-xl-0'>
                <Row>
                  <Col md='6'>
                    <div className='ttl-info text-start'>
                      <H6>
                        <i className='fa fa-envelope me-2'></i> {Email}
                      </H6>
                      <span>{MarekjecnoMailId}</span>
                    </div>
                  </Col>
                  <Col md='6'>
                    <div className='ttl-info text-start ttl-sm-mb-0'>
                      <H6>
                        <i className='fa fa-calendar me-2'></i>
                        {BOD}
                      </H6>
                      <span>{DDMMYY}</span>
                    </div>
                  </Col>
                </Row>
              </Col>
              <Col sm='12' lg='4' className='order-sm-0 order-xl-1'>
                <div className='user-designation'>
                  <div className='title'>
                    <a target='_blank' href='#javascript'>
                      {MarkJecno}
                    </a>
                  </div>
                  <div className='desc mt-2'>{Designer}</div>
                </div>
              </Col>
              <Col sm='6' lg='4' className='order-sm-2 order-xl-2'>
                <Row>
                  <Col md='6'>
                    <div className='ttl-info text-start ttl-xs-mt'>
                      <H6>
                        <i className='fa fa-phone me-2'></i>
                        {ContactUs}
                      </H6>
                      <span>{ContactUsNumber}</span>
                    </div>
                  </Col>
                  <Col md='6'>
                    <div className='ttl-info text-start ttl-sm-mb-0'>
                      <H6>
                        <i className='fa fa-location-arrow me-2'></i>
                        {Location}
                      </H6>
                      <span>{LocationDetails}</span>
                    </div>
                  </Col>
                </Row>
              </Col>
            </Row>
            <hr />
          </div>
        </Card>
      </Col>
    </Fragment>
  );
};

export default UserProfile;
