import React, { Fragment, useContext } from 'react';
import { Col, Row } from 'reactstrap';
import ChatMessage from './ChatMessage';
import ChatMenu from './ChatMenu';
import ChatHeader from './ChatHeader';
import SendChat from './SendChat';
import ChatAppContext from '../../../../_helper/Chat';

const Chatting = () => {
  const { menuToggle } = useContext(ChatAppContext);

  return (
    <Fragment>
      <Row className='chat-box'>
        <Col className='pe-0 chat-right-aside'>
          <div className='chat'>
            <ChatHeader />
            <ChatMessage />
            <SendChat />
          </div>
        </Col>
        <Col className={`ps-0 chat-menu ${menuToggle ? 'show' : ''}`}>
          <ChatMenu />
        </Col>
      </Row>
    </Fragment>
  );
};
export default Chatting;
