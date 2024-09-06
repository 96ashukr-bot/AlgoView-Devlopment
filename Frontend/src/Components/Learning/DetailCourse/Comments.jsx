import { H4, H6, Image, LI, P, UL } from '../../../AbstractElements';
import { JolioMark } from '../../../Constant';
import React, { Fragment } from 'react';
import { Col, Media, Row } from 'reactstrap';

const Comments = () => {
  return (
    <Fragment>
      <H4>Comment</H4>
      <UL attrUL={{ className: 'simple-list' }}>
        <LI attrLI={{ className: 'border-0  bg-transparent' }}>
          <Media className='align-self-center'>
            <Image attrImage={{ className: 'align-self-center', src: `${require('../../../assets/images/blog/comment.jpg')}`, alt: '' }} />
            <Media body>
              <Row>
                <Col md='4' className='xl-100'>
                  <H6 attrH6={{ className: 'mt-0' }}>
                    {JolioMark}
                    <span> {'( Designer )'}</span>
                  </H6>
                </Col>
                <Col md='8' className='xl-100'>
                  <UL attrUL={{ className: 'simple-list border-0 comment-social float-start float-md-end learning-comment flex-row' }}>
                    <LI attrLI={{ className: 'digits bg-transparent' }}>
                      <i className='icofont icofont-thumbs-up'></i>
                      {'02 Hits'}
                    </LI>
                    <LI attrLI={{ className: 'digits bg-transparent' }}>
                      <i className='icofont icofont-ui-chat'></i>
                      {'598 Comments'}
                    </LI>
                  </UL>
                </Col>
              </Row>
              <P>{"There are many variations of passages of Lorem Ipsum available, but the majority have suffered alteration in some form, by injected humour, or randomised words which don't look even slightly believable. If you are going to use a passage of Lorem Ipsum, you need to be sure there isn't anything embarrassing hidden in the middle of text."}</P>
            </Media>
          </Media>
        </LI>
        <LI attrLI={{ className: 'border-0  bg-transparent' }}>
          <UL>
            <LI attrLI={{ className: 'border-0 ' }}>
              <Media>
                <Image attrImage={{ className: 'align-self-center', src: `${require('../../../assets/images/blog/9.jpg')}`, alt: '' }} />
                <Media body>
                  <Row>
                    <Col xl='12'>
                      <H6 attrH6={{ className: 'mt-0' }}>
                        {JolioMark}
                        <span> {'( Designer )'}</span>
                      </H6>
                    </Col>
                  </Row>
                  <P>{"There are many variations of passages of Lorem Ipsum available, but the majority have suffered alteration in some form, by injected humour, or randomised words which don't look even slightly believable. If you are going to use a passage of Lorem Ipsum, you need to be sure there isn't anything embarrassing hidden in the middle of text."}</P>
                </Media>
              </Media>
            </LI>
          </UL>
        </LI>
        <LI attrLI={{ className: 'border-0  bg-transparent' }}>
          <Media>
            <Image attrImage={{ className: 'align-self-center', src: `${require('../../../assets/images/blog/4.jpg')}`, alt: '' }} />
            <Media body>
              <Row>
                <Col md='4' className='xl-100'>
                  <H6 attrH6={{ className: 'mt-0' }}>
                    {JolioMark}
                    <span> {'( Designer )'}</span>
                  </H6>
                </Col>
                <Col md='8' className='xl-100'>
                  <UL attrUL={{ className: 'simple-list border-0 comment-social float-start float-md-end learning-comment flex-row' }}>
                    <LI attrLI={{ className: 'digits bg-transparent' }}>
                      <i className='icofont icofont-thumbs-up'></i>
                      {'02 Hits'}
                    </LI>
                    <LI attrLI={{ className: 'digits bg-transparent' }}>
                      <i className='icofont icofont-ui-chat'></i>
                      {'598 Comments'}
                    </LI>
                  </UL>
                </Col>
              </Row>
              <P>{"There are many variations of passages of Lorem Ipsum available, but the majority have suffered alteration in some form, by injected humour, or randomised words which don't look even slightly believable. If you are going to use a passage of Lorem Ipsum, you need to be sure there isn't anything embarrassing hidden in the middle of text."}</P>
            </Media>
          </Media>
        </LI>
      </UL>
    </Fragment>
  );
};

export default Comments;
