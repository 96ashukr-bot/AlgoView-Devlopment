import React from 'react';
import { Image, H6 } from '../../../AbstractElements';

const CourseCard = ({ data }) => {
  return (
    <div className='course-wrapper'>
      <div className='course-icon-box'>
        <div className='icon-wrap'>
          <Image attrImage={{ src: require(`../../../assets/images/dashboard-3/course/${data.courseImage}.svg`), alt: 'clock vector' }} />
        </div>
        <Image attrImage={{ className: 'arrow-bg', src: require(`../../../assets/images/dashboard-3/course/back-arrow/${data.arrowImage}.png`), alt: 'sqaure border arrow' }} />
      </div>
      <H6 className='f-14'>{data.title}</H6>
    </div>
  );
};

export default CourseCard;
