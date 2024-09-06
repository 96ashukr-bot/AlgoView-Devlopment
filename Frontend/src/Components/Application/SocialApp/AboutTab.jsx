import React, { Fragment } from 'react';
import { Row, Col, Card } from 'reactstrap';
import RightBar from './RightBar';
import LeftBar from './LeftBar';
import PeopleKnows from './About/PeopleKnows';
import ClassHobbies from './About/ClassHobbies';
import Education from './About/Education';
import AvatarShowcase from './About/AvatarShowcase';
import ActivityLog from './About/ActivityLog';
import HeaderCard from '../../Common/Component/HeaderCard';

const AboutTab = () => {
  return (
    <Fragment>
      <Row>
        <Col xl='3 xl-40 box-col-4' lg='12' md='5'>
          <div className='default-according style-1 faq-accordion job-accordion' id='accordionoc2'>
            <Row>
              <LeftBar />
            </Row>
          </div>
        </Col>
        <Col xl='6 xl-60 box-col-8' lg='12' md='7'>
          <Row>
            <Col sm='12'>
              <Card>
                <HeaderCard title={'Pepole You May Know'} />
                <PeopleKnows />
              </Card>
            </Col>
            <ClassHobbies />
            <Education />
            <AvatarShowcase />
            <ActivityLog />
          </Row>
        </Col>
        <Col xl='3' className='xl-100 box-col-12'>
          <div className='default-according style-1 faq-accordion job-accordion' id='accordionoc3'>
            <Row>
              <RightBar />
            </Row>
          </div>
        </Col>
      </Row>
    </Fragment>
  );
};

export default AboutTab;
