import React from 'react';
import { Card, CardBody, CardHeader } from 'reactstrap';
import { H5 } from '../../../AbstractElements';
import { DailyDropdown, MyCourseTitle } from '../../../Constant';
import { MyCourseData } from '../../../Data/OnlineCourse';
import DropdownCommon from '../../Common/Dropdown';
import CourseCard from './CourseCard';

const MyCourse = () => {
  return (
    <Card className='course-card'>
      <CardHeader className='card-no-border'>
        <div className='header-top'>
          <H5 className='m-0'>{MyCourseTitle}</H5>
          <div className='card-header-right-icon'>
            <DropdownCommon icon={false} options={DailyDropdown} btn={{ caret: true }} />
          </div>
        </div>
      </CardHeader>
      <CardBody className='pt-0'>
        <div className='course-main-card'>
          {MyCourseData.map((item, i) => (
            <CourseCard key={i} data={item} />
          ))}
        </div>
      </CardBody>
    </Card>
  );
};

export default MyCourse;
