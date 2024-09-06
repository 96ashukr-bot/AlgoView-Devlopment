import React, { Fragment } from 'react';
import { User, Video, Volume2 } from 'react-feather';
import { Col, Row } from 'reactstrap';
import { Btn, H2, Image, LI, UL } from '../../../../AbstractElements';
import vidImage from '../../../../assets/images/other-images/caller.jpg';
import vidImage1 from '../../../../assets/images/other-images/receiver-img.jpg';

const VideoHistory = () => {
  return (
    <Fragment>
      <div className='chat-history'>
        <Row>
          <Col className='text-center pe-0 call-content'>
            <div>
              <div className='total-time'>
                <H2 attrH2={{ className: 'digits' }}>36 : 56</H2>
              </div>
              <div className='call-icons'>
                <UL attrUL={{ className: 'simple-list list-inline justify-content-center d-flex flex-row' }}>
                  <LI attrLI={{ className: 'list-inline-item' }}>
                    <a href='#javascript'>
                      <Video />
                    </a>
                  </LI>
                  <LI attrLI={{ className: 'list-inline-item' }}>
                    <a href='#javascript'>
                      <Volume2 />
                    </a>
                  </LI>
                  <LI attrLI={{ className: 'list-inline-item' }}>
                    <a href='#javascript'>
                      <User />
                    </a>
                  </LI>
                </UL>
              </div>
              <Btn attrBtn={{ color: 'danger-gradien', className: 'd-block m-auto btn-lg' }}>END CALL</Btn>
              <div className='receiver-img'>
                <Image attrImage={{ src: `${vidImage1}`, alt: '' }} />
              </div>
            </div>
          </Col>
          <Col sm='7' className='caller-img ps-0'>
            <Image attrImage={{ className: 'img-fluid bg-img-cover', src: `${vidImage}`, alt: '' }} />
          </Col>
        </Row>
      </div>
    </Fragment>
  );
};
export default VideoHistory;
