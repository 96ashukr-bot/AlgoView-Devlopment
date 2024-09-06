import React, { Fragment, useContext, useEffect } from 'react';
import { Image, LI, UL } from '../../../../AbstractElements';
import ChatAppContext from '../../../../_helper/Chat';
import start_conversion from '../../../../assets/images/start-conversion.jpg';

const ChatMessage = () => {
  const { allMemberss, chatss, selectedUserr, currentUserr, fetchChatMemberAsyn, fetchChatAsyn } = useContext(ChatAppContext);
  var images = require.context('../../../../assets/images', true);

  useEffect(() => {
    fetchChatMemberAsyn();
    fetchChatAsyn();
  }, [allMemberss.length === 0, chatss.length === 0]);

  const dynamicImage = (image) => {
    return images(`./${image}`);
  };

  const selectedChat = allMemberss && chatss && selectedUserr ? chatss.find((x) => x.users.includes(currentUserr.id) && x.users.includes(selectedUserr.id)) : null;
  var activeChat = 0;
  // eslint-disable-next-line
  if (selectedUserr != null) activeChat = selectedUserr.id;

  return (
    <Fragment>
      {allMemberss && chatss && selectedUserr ? (
        <div className='chat-history chat-msg-box custom-scrollbar'>
          <UL attrUL={{ className: 'simple-list' }}>
            {selectedChat && selectedChat.messages.length > 0 ? (
              selectedChat.messages.map((item, index) => {
                const participators = allMemberss.find((x) => x.id === item.sender);
                return (
                  <LI attrLI={{ className: 'clearfix border-0' }} key={index}>
                    <div className={`message  ${item.sender !== currentUserr.id ? 'my-message' : 'other-message pull-right '}`}>
                      <Image
                        attrImage={{
                          src: `${dynamicImage(participators.thumb)}`,
                          className: `rounded-circle ${item.sender !== currentUserr.id ? 'float-start' : 'float-end'} chat-user-img img-30`,
                          alt: '',
                        }}
                      />
                      <div className='message-data text-end'>
                        <span className='message-data-time'>{item.time}</span>
                      </div>
                      {item.text}
                    </div>
                  </LI>
                );
              })
            ) : (
              <div>
                <Image
                  attrImage={{
                    className: 'img-fluid',
                    src: `${start_conversion}`,
                    alt: 'start conversion ',
                  }}
                />
              </div>
            )}
          </UL>
        </div>
      ) : (
        <div className='loading'></div>
      )}
    </Fragment>
  );
};
export default ChatMessage;
