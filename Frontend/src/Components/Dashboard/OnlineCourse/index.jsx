import React, { Fragment } from 'react';
import { Col, Container, Row } from 'reactstrap';
import { Breadcrumbs } from '../../../AbstractElements';
import ActiveLessons from './ActiveLessons';
import ActivityHours from './ActivityHours';
import Calender from '../../Common/CommonWidgets/Calender';
import GreetingCard2 from './GreetingCard2';
import GreetingGrid from './GreetingGrid';
import LearningOverview from './LearningOverview';
import MyCourse from './MyCourse';
import TodayProgress from './TodayProgress';
import UpcomingEvents from './UpcomingEvents';
import UpcomingSchedule from './UpcomingSchedule';

const OnlineCourse = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle='Online Course' parent='Dashboard' title='Online Course' />
      <Container fluid={true}>
        <Row>
          <GreetingGrid />
          <Col xxl='2' xl='4' sm='6' className='col-ed-3 box-col-5'>
            <TodayProgress />
          </Col>
          <Col xl='2' className='col-ed-3 d-xxl-block d-sm-none box-col-none'>
            <GreetingCard2 />
          </Col>
          <Col xxl='3' xl='5' sm='6' className='col-ed-5 box-col-5'>
            <Calender />
          </Col>
          <Col xxl='5' xl='7' className='col-ed-7 box-col-7'>
            <LearningOverview />
          </Col>
          <Col xxl='4' xl='7' md='6' className='col-ed-7 box-col-7'>
            <ActivityHours />
          </Col>
          <Col xxl='3' xl='5' md='6' className='col-ed-5 box-col-5'>
            <UpcomingEvents />
          </Col>
          <Col xxl='5' className='col-ed-12 box-col-12'>
            <MyCourse />
          </Col>
          <Col xxl='4' md='7' className='col-ed-6 box-col-7'>
            <UpcomingSchedule />
          </Col>
          <Col xxl='3' md='5' sm='6' className='col-ed-6 box-col-5'>
            <ActiveLessons />
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
};

export default OnlineCourse;
