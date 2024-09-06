import React, { useState } from 'react';
import { CheckCircle } from 'react-feather';
import { Card, CardBody, Col } from 'reactstrap';
import { Btn, P, Image, UL, LI, H6 } from '../../../AbstractElements';
import user from '../../../assets/images/user/user.png';
import { TodoCategoriesList } from './TodoCategoriesList';
const TodoSideBar = () => {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <Col xl='3' className='xl-30 box-col-12'>
      <div className='md-sidebar'>
        <Btn attrBtn={{ onClick: (e) => setIsOpen(!isOpen), color: 'primary', className: 'md-sidebar-toggle' }}>To Do filter</Btn>
        <div className={`md-sidebar-aside job-left-aside custom-scrollbar ${isOpen && 'open'} `}>
          <div className='email-left-aside'>
            <div className='email-left-aside'>
              <Card>
                <CardBody>
                  <div className='email-app-sidebar left-bookmark custom-scrollbar'>
                    <div className='d-flex align-items-center'>
                      <div className='media-size-email'>
                        <Image attrImage={{ className: 'me-3 img-40 rounded-circle', src: user, alt: '' }} />
                      </div>
                      <div className='flex-grow-1'>
                        <H6 attrH6={{ className: 'f-w-600' }}>Mark Jecno</H6>
                        <P>Markjecno@gmail.com</P>
                      </div>
                    </div>
                    <UL attrUL={{ className: 'simple-list nav main-menu' }}>
                      <LI attrLI={{ className: 'border-0 nav-item' }}>
                        <Btn attrBtn={{ color: 'primary', className: 'badge-light justify-content-start text-white d-flex align-items-center btn-mail w-100' }}>
                          <CheckCircle className='me-2' />
                          To Do List
                        </Btn>
                      </LI>
                      {TodoCategoriesList.map((item, i) => (
                        <LI key={i} attrLI={{ className: 'border-0 nav-item' }}>
                          <a href='#javascript'>
                            <span className={`iconbg badge-light-${item.color}`}>{item.icon}</span>
                            <span className='title ms-2'>{item.title}</span>
                            {item.badge && <span className={`badge badge-${item.badgeColor ? item.badgeColor : item.color}`}>{item.badge}</span>}
                          </a>
                        </LI>
                      ))}
                    </UL>
                  </div>
                </CardBody>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </Col>
  );
};

export default TodoSideBar;
