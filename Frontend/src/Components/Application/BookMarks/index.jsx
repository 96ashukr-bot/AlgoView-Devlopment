import React, { Fragment, useContext, useState } from 'react';
import { Card, CardBody, Col, Container, Media, Row } from 'reactstrap';
import { MarkJecno, MARKJENCOEMAIL } from '../../../Constant';
import NavTab from './NavTab';
import { Link } from 'react-router-dom';
import Img from '../../../assets/images/user/user.png';
import { Image, P, H6, Btn, Breadcrumbs } from '../../../AbstractElements';
import BookmarksTabs from './BookmarksTabs';
import CustomizerContext from '../../../_helper/Customizer';

const BookmarksContain = () => {
  const { layoutURL } = useContext(CustomizerContext);
  const [isOpen, setIsOpen] = useState(false);
  return (
    <Fragment>
      <Breadcrumbs mainTitle='Bookmark' parent='Apps' title='Bookmark' />
      <Container fluid={true}>
        <div className='email-wrap bookmark-wrap'>
          <Row>
            <Col xl='3' className=' box-col-6'>
              <div className='email-sidebar'>
                <div className={`email-left-aside`}>
                  <div className='md-sidebar'>
                    <Btn attrBtn={{ onClick: (e) => setIsOpen(!isOpen), color: 'primary', className: 'md-sidebar-toggle' }}>bookmark filter</Btn>
                    <div className={`md-sidebar-aside job-left-aside custom-scrollbar ${isOpen && 'open'}`}>
                      <div className='email-left-aside'>
                        <Card>
                          <CardBody>
                            <div className='email-app-sidebar left-bookmark'>
                              <Media className='align-items-center'>
                                <div className='media-size-email'>
                                  <Image
                                    attrImage={{
                                      className: 'me-3 rounded-circle',
                                      src: `${Img}`,
                                      alt: '',
                                    }}
                                  />
                                </div>
                                <Media body>
                                  <Link to={`/app/users/userprofile/${layoutURL}`}>
                                    <H6 attrH6={{ className: 'f-w-600' }}>{MarkJecno}</H6>
                                  </Link>
                                  <P>{MARKJENCOEMAIL}</P>
                                </Media>
                              </Media>
                              <NavTab />
                            </div>
                          </CardBody>
                        </Card>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Col>
            <Col xl='9' md='12' className='box-col-8'>
              <div className='email-right-aside bookmark-tabcontent'>
                <Card className='email-body radius-left'>
                  <div className='ps-0'>
                    <BookmarksTabs />
                  </div>
                </Card>
              </div>
            </Col>
          </Row>
        </div>
      </Container>
    </Fragment>
  );
};
export default BookmarksContain;
