import React, { Fragment } from 'react';
import { Card, CardBody, Col, Input, InputGroup, Media } from 'reactstrap';
import { Btn, H6, Image, P } from '../../../../AbstractElements';
import { AlexendraDhadio, ELANA, IssaBell, JasonBorne, MoreCommnets, OliviaJon } from '../../../../Constant';
import one from '../../../../assets/images/user/1.jpg';
import three from '../../../../assets/images/user/3.jpg';
import two from '../../../../assets/images/user/2.png';
import timeline1 from '../../../../assets/images/social-app/timeline-1.png';
import { MoreVertical } from 'react-feather';

const NewUserClass = () => {
  return (
    <Fragment>
      <Col sm='12'>
        <Card>
          <CardBody>
            <div className='new-users-social'>
              <Media className='align-items-center'>
                <Image attrImage={{ className: 'rounded-circle image-radius m-r-15', src: `${one}`, alt: '' }} />
                <Media body>
                  <H6 attrH6={{ className: 'mb-0 f-w-700' }}>{ELANA}</H6>
                  <P>{'January, 12,2022'}</P>
                </Media>
                <span className='pull-right mt-0'>
                  <MoreVertical />
                </span>
              </Media>
            </div>
            <Image attrImage={{ className: 'img-fluid', alt: '', src: `${timeline1}` }} />
            <div className='timeline-content'>
              <P>{'Vibrant horizontal stripes pattern cool soft cotton fabric front zipper snuggly jersey-lined hood robust cuffs and twin pockets. Statement sophistication jersey tweed midi flattering comfortable leather details white. '}</P>
              <div className='like-content'>
                <span>
                  <i className='fa fa-heart font-danger'></i>
                </span>
                <span className='pull-right comment-number'>
                  <span>{'20'} </span>
                  <span>
                    <i className='fa fa-share-alt me-0'></i>
                  </span>
                </span>
                <span className='pull-right comment-number'>
                  <span>{'10'} </span>
                  <span>
                    <i className='fa fa-comments-o'></i>
                  </span>
                </span>
              </div>
              <div className='social-chat'>
                <div className='your-msg'>
                  <Media>
                    <Image attrImage={{ className: 'img-50 img-fluid m-r-20 rounded-circle', alt: '', src: `${one}` }} />
                    <Media body>
                      <span className='f-w-500'>
                        {JasonBorne}{' '}
                        <span>
                          {'1 Year Ago'} <i className='fa fa-reply font-primary'></i>
                        </span>
                      </span>
                      <P>{'we are doing dance and singing songs, please vote our post which is very good for all young peoples'}</P>
                    </Media>
                  </Media>
                </div>
                <div className='other-msg'>
                  <Media>
                    <Image attrImage={{ className: 'img-50 img-fluid m-r-20 rounded-circle', alt: '', src: `${two}` }} />
                    <Media body>
                      <span className='f-w-500'>
                        {AlexendraDhadio}{' '}
                        <span>
                          {'1 Month Ago'} <i className='fa fa-reply font-primary'></i>
                        </span>
                      </span>
                      <P>{'ohh yeah very good car and its features i will surely vote for it'} </P>
                    </Media>
                  </Media>
                </div>
                <div className='other-msg'>
                  <Media>
                    <Image attrImage={{ className: 'img-50 img-fluid m-r-20 rounded-circle', alt: '', src: `${three}` }} />
                    <Media body>
                      <span className='f-w-500'>
                        {OliviaJon}{' '}
                        <span>
                          {'15 Days Ago'} <i className='fa fa-reply font-primary'></i>
                        </span>
                      </span>
                      <P>{'ohh yeah very good car and its features i will surely vote for it'} </P>
                    </Media>
                  </Media>
                </div>
                <div className='your-msg'>
                  <Media>
                    <Image attrImage={{ className: 'img-50 img-fluid m-r-20 rounded-circle', alt: '', src: `${one}` }} />
                    <Media body>
                      <span className='f-w-500'>
                        {IssaBell}{' '}
                        <span>
                          {'1 Year Ago'} <i className='fa fa-reply font-primary'></i>
                        </span>
                      </span>
                      <P>{'we are doing dance and singing songs, please vote our post which is very good for all young peoples'}</P>
                    </Media>
                  </Media>
                </div>
                <div className='text-center'>
                  <a href='#javascript'>{MoreCommnets}</a>
                </div>
              </div>
              <div className='comments-box'>
                <Media>
                  <Image attrImage={{ className: 'img-50 img-fluid m-r-20 rounded-circle', alt: '', src: `${one}` }} />
                  <Media body>
                    <InputGroup className='text-box'>
                      <Input className='form-control input-txt-bx' type='text' name='message-to-send' placeholder='Post Your commnets' />
                      <div className='input-group-append'>
                        <Btn attrBtn={{ color: 'transparent' }}>
                          <i className='fa fa-smile-o'> </i>
                        </Btn>
                      </div>
                    </InputGroup>
                  </Media>
                </Media>
              </div>
            </div>
          </CardBody>
        </Card>
      </Col>
    </Fragment>
  );
};

export default NewUserClass;
