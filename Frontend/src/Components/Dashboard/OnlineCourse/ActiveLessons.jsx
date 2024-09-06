import React from 'react';
import { ArrowRight } from 'react-feather';
import { Link } from 'react-router-dom';
import { Card, CardBody, CardHeader } from 'reactstrap';
import { H5, UL, LI, H6, Image } from '../../../AbstractElements';
import { ActiveLessonsTitle, View } from '../../../Constant';
import { ActiveLessonsList } from '../../../Data/OnlineCourse';
import LessonChart from './LessonChart';

const ActiveLessons = () => {
  return (
    <Card>
      <CardHeader className='card-no-border'>
        <div className='header-top'>
          <H5 attrH5={{ className: 'm-0' }}>{ActiveLessonsTitle}</H5>
          <div className='card-header-right-icon'>
            <Link className='link-only' to='#javascript'>
              {View} <ArrowRight />
            </Link>
          </div>
        </div>
      </CardHeader>
      <CardBody className='pt-0'>
        <UL attrUL={{ className: 'lessons-lists' }}>
          {ActiveLessonsList.map((item, i) => (
            <LI key={i}>
              <Image attrImage={{ src: require(`../../../assets/images/dashboard-3/lessons/${item.image}`), alt: 'ux icon' }} />
              <div>
                <H6 className='f-14 f-w-400 mb-0'>{item.title}</H6>
                <span className='f-light'>{item.subTitle}</span>
              </div>
              <div className='lesson-wrap ms-auto'>
                <LessonChart chartData={item.chart} />
              </div>
            </LI>
          ))}
        </UL>
      </CardBody>
    </Card>
  );
};

export default ActiveLessons;
