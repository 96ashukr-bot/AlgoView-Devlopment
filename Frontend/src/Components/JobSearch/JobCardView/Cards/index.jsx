import { H6, Image, P } from '../../../../AbstractElements';
import JobSearchContext from '../../../../_helper/JobSearch';
import React, { Fragment, useContext } from 'react';
import { Card, Col, Row, CardBody } from 'reactstrap';
import { Link } from 'react-router-dom';
import CustomizerContext from '../../../../_helper/Customizer';
import PagesSort from './Pagination';

const CardsClass = () => {
  const { layoutURL } = useContext(CustomizerContext);
  const { jobData } = useContext(JobSearchContext);
  return (
    <Fragment>
      <Col xl='9' className='box-col-8 xl-60'>
        <Row className='mb-5'>
          {jobData &&
            jobData.map((item, i) => (
              <Col xl='6' className='xl-100 box-col-12' key={i}>
                <Card className={`${item.ribbion ? 'ribbon-vertical-left-wrapper' : ''}`}>
                  {item.ribbion ? (
                    <div className='ribbon ribbon-bookmark ribbon-vertical-left ribbon-secondary'>
                      <i className='icofont icofont-love'></i>
                    </div>
                  ) : (
                    ''
                  )}
                  <div className='job-search'>
                    <CardBody>
                      <div className='media'>
                        <Image attrImage={{ className: 'img-40 img-fluid m-r-20', src: `${require(`../../../../assets/images/${item.logo}`)}`, alt: '' }} />
                        <div className='media-body'>
                          <H6 attrH6={{ className: 'f-w-600' }}>
                            <Link to={`/app/jobSearch/job-detail/${layoutURL}`}>{item.job_name}</Link>
                            {item.badgeValue ? <span className='badge badge-primary pull-right'>New</span> : <span className='pull-right'>2 days ago</span>}
                          </H6>
                          <P>
                            {item.job_area}, {item.job_city}
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
                      <P>{item.Job_description}</P>
                    </CardBody>
                  </div>
                </Card>
              </Col>
            ))}
          <PagesSort />
        </Row>
      </Col>
    </Fragment>
  );
};

export default CardsClass;
