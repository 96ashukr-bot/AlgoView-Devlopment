import React from 'react';
import { Link } from 'react-router-dom';
import { Card, CardBody } from 'reactstrap';
import { H4 } from '../../../AbstractElements';

import SvgIcon from '../Component/SvgIcon';
import SquareGroupUi from '../../Dashboard/OnlineCourse/SquareGroupUi';

const CourseBox = ({ data, mainClass }) => {
  return (
    <Card className={`course-box ${mainClass ? mainClass : ''}`}>
      <CardBody>
        <div className='course-widget'>
          <div className={`course-icon ${data.color ? data.color : ''}`}>
            <SvgIcon className='fill-icon' iconId={data.icon} />
          </div>
          <div>
            <H4 attrH4={{ className: 'mb-0' }}>{data.course}</H4>
            <span className='f-light'>{data.title}</span>
            <Link className='btn btn-light f-light' to={`/learning/learning-list-view`}>
              {data.link}
              <span className='ms-2'>
                <SvgIcon className='fill-icon f-light' iconId='arrowright' />
              </span>
            </Link>
          </div>
        </div>
      </CardBody>
      <SquareGroupUi />
    </Card>
  );
};

export default CourseBox;
