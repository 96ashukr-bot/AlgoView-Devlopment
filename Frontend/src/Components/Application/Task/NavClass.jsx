import React, { Fragment, useCallback, useState } from 'react';
import { Col, Card, CardBody, Nav, NavItem } from 'reactstrap';
import { Views, Tags } from '../../../Constant';
import { PlusCircle } from 'react-feather';
import NewTaskClass from './NewTask';
import HeaderProfile from './HeaderProfile';
import { taskData, tagData } from '../../Common/Data/Task';
import CreateTag from './CreateTag';
import { Btn } from '../../../AbstractElements';

const NavClass = ({ activeToggle }) => {
  const [activeTab, setActiveTab] = useState('1');
  const [tagModal, setTagModal] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const tagToggle = () => setTagModal(!tagModal);

  const tagCallback = useCallback((modal) => {
    setTagModal(modal);
  });

  return (
    <Fragment>
      <Col xl='3' className='box-col-4'>
        <div className='md-sidebar'>
          <Btn attrBtn={{ onClick: (e) => setIsOpen(!isOpen), color: 'primary', className: 'md-sidebar-toggle' }}>contact filter</Btn>
          <div className={`md-sidebar-aside job-left-aside custom-scrollbar ${isOpen && 'open'}`}>
            <div className='email-sidebar'>
              <div className={`email-left-aside`}>
                <Card>
                  <CardBody>
                    <div className='email-app-sidebar left-bookmark'>
                      <HeaderProfile />
                      <Nav className='main-menu' role='tablist'>
                        <NavItem>
                          <NewTaskClass />
                        </NavItem>
                        <NavItem>
                          <span className='main-title'>{Views}</span>
                        </NavItem>
                        {taskData.map((item) => (
                          <NavItem key={item.id}>
                            <a
                              href='#javaScript'
                              className={activeTab === item.activeTab ? 'active' : ''}
                              onClick={() => {
                                setActiveTab(item.activeTab);
                                activeToggle(item.activeTab);
                              }}>
                              <span className='title'> {item.title}</span>
                            </a>
                          </NavItem>
                        ))}
                        <li>
                          <hr />
                        </li>
                        <NavItem>
                          <span className='main-title'>
                            {' '}
                            {Tags}
                            <span className='pull-right' onClick={tagToggle}>
                              <PlusCircle />
                            </span>
                          </span>
                        </NavItem>
                        <CreateTag tagCallback={tagCallback} tagModal={tagModal} />
                        {tagData.map((item) => (
                          <Fragment key={item.id}>
                            <NavItem>
                              <a
                                href='#javaScript'
                                className={activeTab === item.activeTab ? 'show' : ''}
                                onClick={() => {
                                  setActiveTab(item.activeTab);
                                  activeToggle(item.activeTab);
                                }}>
                                <span className='title'> {item.title}</span>
                              </a>
                            </NavItem>
                          </Fragment>
                        ))}
                      </Nav>
                    </div>
                  </CardBody>
                </Card>
              </div>
            </div>
          </div>
        </div>
      </Col>
    </Fragment>
  );
};

export default NavClass;
