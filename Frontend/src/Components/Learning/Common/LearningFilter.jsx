import React, { Fragment, useState } from 'react';
import { Row, Col } from 'reactstrap';
import FindCourseClass from './FindCourse';
import CategoriesClass from './Categories';
import UpcomingClass from './UpcomingClass';
import { Btn } from '../../../AbstractElements';

const LearningFilter = () => {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <Fragment>
      <Col xl='3' className='xl-40 box-col-12 learning-filter order-1 order-xl-2'>
        <div className='md-sidebar'>
          <Btn attrBtn={{ onClick: (e) => setIsOpen(!isOpen), color: 'primary', className: 'md-sidebar-toggle' }}>Learning filter</Btn>
          <div className={`md-sidebar-aside job-left-aside custom-scrollbar ${isOpen && 'open'} `}>
            <div className='default-according style-1 faq-accordion job-accordion' id='accordionoc'>
              <Row>
                <FindCourseClass />
                <CategoriesClass />
                <UpcomingClass />
              </Row>
            </div>
          </div>
        </div>
      </Col>
    </Fragment>
  );
};

export default LearningFilter;
