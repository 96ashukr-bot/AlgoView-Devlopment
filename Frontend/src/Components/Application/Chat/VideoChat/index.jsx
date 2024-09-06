import React, { Fragment, useContext } from 'react';
import { Card, CardBody, Col, Container, Row } from 'reactstrap';
import ChatMenu from '../ChatApp/ChatMenu';
import { Breadcrumbs } from '../../../../AbstractElements';
import ChatStatus from './ChatStatus';
import VideoHistory from './VideoHistory';
import ChatHeader from '../ChatApp/ChatHeader';
import ChatAppContext from '../../../../_helper/Chat';

const VideoChatContain = () => {
  const { menuToggle } = useContext(ChatAppContext);
  return (
    <Fragment>
      <Breadcrumbs mainTitle='Video Chat' parent='Chat' title='Video Chat' />
      <Container fluid={true}>
        <Row>
          <Col className='call-chat-sidebar'>
            <Card>
              <CardBody className='chat-body'>
                <ChatStatus />
              </CardBody>
            </Card>
          </Col>
          <Col className='call-chat-body'>
            <Card>
              <CardBody className='p-0'>
                <Row className='chat-box'>
                  <Col className=' pe-xl-0 chat-right-aside'>
                    <div className='chat'>
                      <ChatHeader />
                      <VideoHistory />
                    </div>
                  </Col>
                  <Col className={`ps-xl-0 chat-menu ${menuToggle ? 'show' : ''}`}>
                    <ChatMenu />
                  </Col>
                </Row>
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
};
export default VideoChatContain;
