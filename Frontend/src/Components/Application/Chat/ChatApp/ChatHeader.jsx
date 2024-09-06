import React, { Fragment, useContext } from 'react';
import { Image, UL, LI } from '../../../../AbstractElements';
import ChatAppContext from '../../../../_helper/Chat';
import { AlignJustify, Headphones, Paperclip, Search, Video } from 'react-feather';
import { useLocation } from 'react-router-dom';

const ChatHeader = () => {
  const { selectedUserr, setMenuToggle, menuToggle } = useContext(ChatAppContext);
  const location = useLocation();

  const chatMenuToggle = () => {
    setMenuToggle(!menuToggle);
  };
  return (
    <Fragment>
      <div className='chat-header clearfix'>
        <Image
          attrImage={{
            className: 'rounded-circle',
            src: `${require(`../../../../assets/images/${selectedUserr ? selectedUserr.thumb : 'user/8.jpg'}`)}`,
            alt: '',
          }}
        />
        <div className='media-body'>
          <div className='about'>
            <div className='name'>
              {selectedUserr ? selectedUserr.name : 'Vincent Porter'}
              {location.state3 ? <span className='font-primary f-12'> Typing...</span> : ''}
            </div>
            <div className='status digits'>{selectedUserr ? selectedUserr.lastSeenDate : '5 May, 5:30 PM'}</div>
          </div>
        </div>
        <UL attrUL={{ className: 'simple-list list-inline float-start float-sm-end chat-menu-icons d-flex flex-row' }}>
          <LI attrLI={{ className: 'list-inline-item border-0' }}>
            <a href='#javascript'>
              <Search />
            </a>
          </LI>
          <LI attrLI={{ className: 'list-inline-item border-0' }}>
            <a href='#javascript'>
              <Paperclip />
            </a>
          </LI>
          <LI attrLI={{ className: 'list-inline-item border-0' }}>
            <a href='#javascript'>
              <Headphones />
            </a>
          </LI>
          <LI attrLI={{ className: 'list-inline-item border-0' }}>
            <a href='#javascript'>
              <Video />
            </a>
          </LI>
          <LI attrLI={{ className: 'list-inline-item toogle-bar border-0' }}>
            <a href='#javascript'>
              <AlignJustify onClick={() => chatMenuToggle()} />
            </a>
          </LI>
        </UL>
      </div>
    </Fragment>
  );
};
export default ChatHeader;
