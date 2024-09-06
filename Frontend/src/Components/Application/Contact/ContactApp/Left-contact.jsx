import React, { Fragment, useState, useCallback } from 'react';
import { Col, Card, CardBody } from 'reactstrap';
import { Btn } from '../../../../AbstractElements';
import HeaderProfile from './HeaderProfile';
import NavComponent from './NavComponent';
import TabComponent from './TabComponent';

const LeftContact = () => {
  const [activeTab, setActiveTab] = useState('1');
  const [isOpen, setIsOpen] = useState(false);
  const callback = useCallback((tab) => {
    setActiveTab(tab);
  }, []);

  return (
    <Fragment>
      <Col xl='3' className='box-col-6'>
        <div className='md-sidebar'>
          <Btn attrBtn={{ onClick: (e) => setIsOpen(!isOpen), color: 'primary', className: 'md-sidebar-toggle' }}>contact filter</Btn>
          <div className={`md-sidebar-aside job-left-aside custom-scrollbar ${isOpen && 'open'}`}>
            <div className='email-sidebar'>
              <div className={`email-left-aside`}>
                <Card>
                  <CardBody>
                    <div className='email-app-sidebar left-bookmark'>
                      <HeaderProfile />
                      <NavComponent callbackActive={callback} />
                    </div>
                  </CardBody>
                </Card>
              </div>
            </div>
          </div>
        </div>
      </Col>
      <Col xl='9' md='12' className='box-col-12'>
        <div className='email-right-aside bookmark-tabcontent contacts-tabs'>
          <div className='email-body radius-left'>
            <div className='ps-0'>
              <TabComponent activeTab={activeTab} />
            </div>
          </div>
        </div>
      </Col>
    </Fragment>
  );
};

export default LeftContact;
