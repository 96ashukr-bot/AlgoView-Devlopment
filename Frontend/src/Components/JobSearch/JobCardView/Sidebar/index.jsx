import React, { Fragment, useState } from 'react';
import { Col, Row } from 'reactstrap';
import Filter from './Filter';
import Location from './Location';
import JobTitleClass from './JobTitle';
import Industry from './Industry';
import SkillClass from './Skill';
import { Btn } from '../../../../AbstractElements';

const Sidebar = () => {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <Fragment>
      <Col xl='3' className='box-col-4 xl-40'>
        <div className='md-sidebar'>
          <Btn attrBtn={{ onClick: (e) => setIsOpen(!isOpen), color: 'primary', className: 'md-sidebar-toggle' }}>Job filter</Btn>
          <div className={`md-sidebar-aside job-left-aside custom-scrollbar ${isOpen && 'open'} `}>
            <div className='default-according style-1 faq-accordion job-accordion' id='accordionoc'>
              <Row>
                <Filter />
                <Location />
                <JobTitleClass />
                <Industry />
                <SkillClass />
              </Row>
            </div>
          </div>
        </div>
      </Col>
    </Fragment>
  );
};

export default Sidebar;
