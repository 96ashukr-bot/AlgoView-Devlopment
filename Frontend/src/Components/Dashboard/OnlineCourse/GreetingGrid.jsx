import React from 'react';
import { Col, Row } from 'reactstrap';
import { CourseBoxData } from '../../../Data/OnlineCourse';
import CourseBox from '../../Common/CommonWidgets/CourseBox';
import GreetingCard from './GreetingCard';

const GreetingGrid = () => {
  return (
    <Col xxl='5' xl='8' className='col-ed-6 box-col-7'>
      <Row>
        <Col sm='12'>
          <GreetingCard />
        </Col>
        {CourseBoxData.map((item, i) => (
          <Col sm='6' key={i}>
            <CourseBox data={item} />
          </Col>
        ))}
      </Row>
    </Col>
  );
};

export default GreetingGrid;
