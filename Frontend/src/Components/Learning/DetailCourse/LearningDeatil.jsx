import Comments from './Comments';
import BlogDetails from './BlogDetails';
import React, { Fragment } from 'react';
import { Col } from 'reactstrap';

const LearningDeatil = () => {
  return (
    <Fragment>
      <Col xl='9' className='box-col-8 xl-60 order-2 order-xl-1'>
        <div className='blog-single'>
          <BlogDetails />
          <div className='comment-box'>
            <Comments />
          </div>
        </div>
      </Col>
    </Fragment>
  );
};

export default LearningDeatil;
