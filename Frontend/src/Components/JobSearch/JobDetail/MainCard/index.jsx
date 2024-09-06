import ListCard from '../../ListView/ListCard';
import { H6, P, Btn, Image } from '../../../../AbstractElements';
import JobDescription from './jobDescription';
import React, { Fragment, useContext } from 'react';
import { Card, Col, CardBody, Row } from 'reactstrap';
import { Link } from 'react-router-dom';
import CustomizerContext from '../../../../_helper/Customizer';

const MainCard = () => {
  const { layoutURL } = useContext(CustomizerContext);

  return (
    <Fragment>
      <Col xl='9' className='box-col-8 xl-60'>
        <Card>
          <div className='job-search'>
            <CardBody>
              <div className='media'>
                <Image attrImage={{ className: 'img-40 img-fluid m-r-20', src: `${require('../../../../assets/images/job-search/1.jpg')}`, alt: '' }} />
                <div className='media-body'>
                  <H6 attrH6={{ className: 'f-w-600' }}>
                    <a href='#javascript'>Product Designer (UI/UX Designer)</a>
                    <span className='pull-right'>
                      <Link to={`/app/jobsearch/jobapply/${layoutURL}`}>
                        <Btn attrBtn={{ className: 'btn btn-sm job-apply-btn', color: 'primary' }}>Apply for this job</Btn>
                      </Link>
                    </span>
                  </H6>
                  <P>
                    Cuba - United States
                    <span>
                      <i className='fa fa-star font-warning'></i>
                      <i className='fa fa-star font-warning'></i>
                      <i className='fa fa-star font-warning'></i>
                      <i className='fa fa-star font-warning'></i>
                      <i className='fa fa-star font-warning'></i>
                    </span>
                  </P>
                </div>
              </div>
              <JobDescription />
            </CardBody>
          </div>
        </Card>
        <div className='header-faq'>
          <H6 attrH6={{ className: 'mb-0 f-w-600' }}>Similar jobs</H6>
        </div>
        <Row>
          <ListCard />
        </Row>
      </Col>
    </Fragment>
  );
};

export default MainCard;
