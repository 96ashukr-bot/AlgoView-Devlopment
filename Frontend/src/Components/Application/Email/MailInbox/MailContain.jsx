import React, { Fragment, useContext } from 'react';
import { Row, Media, Label, Input, Col, Form, FormGroup } from 'reactstrap';
import { Btn, H5, H6, Image, LI, P, UL } from '../../../../AbstractElements';
import { NewMessage, To, ATTACHMENTS, DownloadAll, Reply, ReplyAll, Forward, Send, Messages, Subject } from '../../../../Constant';
import CKEditor from 'react-ckeditor-component';
import email1 from '../../../../assets/images/email/1.jpg';
import email2 from '../../../../assets/images/email/2.jpg';
import email3 from '../../../../assets/images/email/3.jpg';
import EmailContext from '../../../../_helper/Email';

var images = require.context('../../../../assets/images', true);

const MailContain = () => {
  const { singleMailRecord, compose } = useContext(EmailContext);

  const dynamicImage = (image) => {
    return images(`./${image}`);
  };
  return (
    <Fragment>
      <Col xl='8' md='12' className='box-md-12 pl-0'>
        <div className='email-right-aside'>
          <div className='email-body radius-left'>
            <div className='ps-0'>
              <div className='tab-content'>
                <div className={`tab-pane fade ${compose ? 'active show' : ''}`} id='pills-darkhome' role='tabpanel' aria-labelledby='pills-darkhome-tab'>
                  <div className='email-compose'>
                    <div className='email-top'>
                      <Row>
                        <Col sm='8 xl-50'>
                          <h4 className='mb-0'>{NewMessage}</h4>
                        </Col>
                        <Col sm='4 xl-50' className='btn-middle text-end'>
                          <Btn attrBtn={{ color: 'primary', className: 'btn-mail text-center mb-0 mt-0' }}>
                            <i className='fa fa-paper-plane me-2'></i>
                            {Send}
                          </Btn>
                        </Col>
                      </Row>
                    </div>
                    <div className='email-wrapper'>
                      <Form className='theme-form'>
                        <FormGroup>
                          <Label className='col-form-Label pt-0'>{To}</Label>
                          <Input className='form-control' type='email' />
                        </FormGroup>
                        <FormGroup>
                          <Label>{Subject}</Label>
                          <Input className='form-control' type='text' />
                        </FormGroup>
                        <div>
                          <Label className='text-muted'>{Messages}</Label>
                          <CKEditor className='email-compose-ck' activeclassName='p10' />
                        </div>
                      </Form>
                    </div>
                  </div>
                </div>
                <div className={`tab-pane fade ${compose !== true ? 'active show' : ''}`}>
                  <div className='email-content'>
                    <div className='email-top'>
                      <Row>
                        <Col md='6 xl-100' sm='12'>
                          <Media className='align-items-center'>
                            <Image attrImage={{ className: 'me-3 rounded-circle img-50', src: `${singleMailRecord.image ? dynamicImage(singleMailRecord.image) : ''}`, alt: '' }} />
                            <Media body>
                              <H6>
                                {singleMailRecord.name}{' '}
                                <small>
                                  <span className='digits'>({singleMailRecord.date})</span> <span className='digits'>6:00</span> AM
                                </small>
                              </H6>
                              <P>{singleMailRecord.cc}</P>
                            </Media>
                          </Media>
                        </Col>
                        <Col md='6' sm='12'>
                          <div className='float-end d-flex'>
                            <P attrPara={{ className: 'user-emailid' }}>
                              {'Lormlpsa'}
                              <span className='digits'>{'23'}</span>
                              {'@company.com'}
                            </P>
                            <i className={`fa fa-star-o f-18 mt-1 ${singleMailRecord.favourite ? 'starred' : ''} `}></i>
                          </div>
                        </Col>
                      </Row>
                    </div>
                    <div className='email-wrapper'>
                      <P>{'Hello'}</P>
                      <P>{'Dear Sir Good Morning'},</P>
                      <H5>{'Elementum varius nisi vel tempus. Donec eleifend egestas viverra.'}</H5>
                      <P attrPara={{ className: 'm-b-20' }}>
                        {
                          'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur non diam facilisis, commodo libero et, commodo sapien. Pellentesque sollicitudin massa sagittis dolor facilisis, sit amet vulputate nunc molestie. Pellentesque maximus nibh id luctus porta. Ut consectetur dui nec nulla mattis luctus. Donec nisi diam, congue vitae felis at, ullamcorper bibendum tortor. Vestibulum pellentesque felis felis. Etiam ac tortor felis. Ut elit arcu, rhoncus in laoreet vel, gravida sed tortor.'
                        }
                      </P>
                      <P>{'In elementum varius nisi vel tempus. Donec eleifend egestas viverra. Donec dapibus sollicitudin blandit. Donec scelerisque purus sit amet feugiat efficitur. Quisque feugiat semper sapien vel hendrerit. Mauris lacus felis, consequat nec pellentesque viverra, venenatis a lorem. Sed urna lectus.Quisque feugiat semper sapien vel hendrerit'}</P>
                      <hr />
                      <div className='d-inline-block'>
                        <H6 className='text-muted'>
                          <i className='icofont icofont-clip'></i> {ATTACHMENTS}
                        </H6>
                        <a className='text-muted text-end right-download' href='#javascript'>
                          <i className='fa fa-long-arrow-down me-2'></i>
                          {DownloadAll}
                        </a>
                        <div className='clearfix'></div>
                      </div>
                      <div className='attachment'>
                        <UL attrUL={{ className: 'list-inline d-flex flex-row' }}>
                          <LI attrLI={{ className: 'list-inline-item border-0' }}>
                            <Image attrImage={{ className: 'img-fluid', src: `${email1}`, alt: '' }} />
                          </LI>
                          <LI attrLI={{ className: 'list-inline-item border-0' }}>
                            <Image attrImage={{ className: 'img-fluid', src: `${email2}`, alt: '' }} />
                          </LI>
                          <LI attrLI={{ className: 'list-inline-item border-0' }}>
                            <Image attrImage={{ className: 'img-fluid', src: `${email3}`, alt: '' }} />
                          </LI>
                        </UL>
                      </div>
                      <hr />
                      <div className='action-wrapper'>
                        <UL attrUL={{ className: 'actions flex-row' }}>
                          <LI arreLI={{ className: 'border-0' }}>
                            <a className='text-muted' href='#javascript'>
                              <i className='fa fa-reply me-2'></i>
                              {Reply}
                            </a>
                          </LI>
                          <LI arreLI={{ className: 'border-0' }}>
                            <a className='text-muted' href='#javascript'>
                              <i className='fa fa-reply-all me-2'></i>
                              {ReplyAll}
                            </a>
                          </LI>
                          <LI arreLI={{ className: 'border-0' }}>
                            <a className='text-muted' href='#javascript'>
                              <i className='fa fa-share me-2'></i>
                            </a>
                            {Forward}
                          </LI>
                        </UL>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Col>
    </Fragment>
  );
};
export default MailContain;
