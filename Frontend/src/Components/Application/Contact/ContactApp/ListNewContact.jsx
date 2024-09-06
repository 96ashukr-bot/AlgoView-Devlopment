import React, { Fragment, useState } from 'react';
import { H6, Image, P } from '../../../../AbstractElements';
import { Col, Nav, NavLink } from 'reactstrap';
import CreateContact from './CreateContact';

const ListNewContact = ({ users, userCallback }) => {
  const [dynamictab, setDynamicTab] = useState('0');

  const ContactDetails = (user) => {
    userCallback({ id: user.id, name: user.name, surname: user.surname, avatar: user.avatar, age: user.age, mobile: user.mobile });
  };

  return (
    <Fragment>
      <Col xl='4' md='5' className='xl-50'>
        <Nav tag='div' className='flex-column nav-pills'>
          {users.length > 0 ? (
            users.map((user, index) => {
              return (
                <NavLink className={dynamictab === index ? 'active' : ''} onClick={() => setDynamicTab(index)} key={index}>
                  <div className='media' onClick={() => ContactDetails(user)}>
                    <Image attrImage={{ className: 'p-0 img-fluid img-50 m-r-20 rounded-circle update_img_0', src: `${user.avatar}`, alt: '' }} />
                    <div className='media-body'>
                      <H6>
                        <span className='first_name_0'>{user.name}</span>&nbsp;
                        <span className='last_name_0'>{user.surname}</span>
                      </H6>
                      <P attrPara={{ className: 'email_add_0' }}>
                        {user.name}
                        {'@gmail.com'}
                      </P>
                    </div>
                  </div>
                </NavLink>
              );
            })
          ) : (
            <div className='p-4'>
              You need to create new contact.Please click on button.
              <CreateContact empty={users.length > 0 ? true : false}>
                <b>New Contact</b>
              </CreateContact>
            </div>
          )}
        </Nav>
      </Col>
    </Fragment>
  );
};

export default ListNewContact;
