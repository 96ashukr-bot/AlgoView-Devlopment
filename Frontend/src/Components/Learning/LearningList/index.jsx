import { Breadcrumbs } from '../../../AbstractElements';
import LearningFilter from '../Common/LearningFilter';
import BlogBox from './BlogBox';
import BoxList from './BoxList';
import React, { Fragment } from 'react';
import { Container, Row, Col } from 'reactstrap';

const LearningList = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle='Learning List' parent='Learning' title='Learning List' />
      <Container fluid={true}>
        <Row className='learning-block'>
          <Col xl='9' className='xl-60 box-col-8 order-2 order-xl-1'>
            <Row>
              <BlogBox />
              <BoxList />
            </Row>
          </Col>
          <LearningFilter />
        </Row>
      </Container>
    </Fragment>
  );
};

export default LearningList;
