import JobSearchContext from '../../../_helper/JobSearch';
import { H6, Image, P } from '../../../AbstractElements';
import React, { Fragment, useContext } from 'react';
import { Card, Col, CardBody } from 'reactstrap';
import { Link } from 'react-router-dom';
import CustomizerContext from '../../../_helper/Customizer';
import Pagination from '../JobCardView/Cards/Pagination';

const ListCard = ({ colClass }) => {
  const { jobData } = useContext(JobSearchContext);
  const { layoutURL } = useContext(CustomizerContext);

  return (
    <Fragment>
      <Col className={colClass}>
        {jobData &&
          jobData.slice(0, 8).map((item, i) => (
            <Card key={i} className={`${item.ribbion ? 'ribbon-vertical-left-wrapper' : ''}`}>
              {item.ribbion ? (
                <div className='ribbon ribbon-bookmark ribbon-vertical-left ribbon-primary'>
                  <i className='icofont icofont-globe-alt'></i>
                </div>
              ) : (
                ''
              )}
              <div className='job-search'>
                <CardBody>
                  <div className='media'>
                    <Image attrImage={{ className: 'img-40 img-fluid m-r-20', src: `${require(`../../../assets/images/${item.logo}`)}`, alt: '' }} />
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
                  <P>We are looking for an experienced and Web designer and/or frontend engineer with expertise in accessibility to join our team, 3+ years of experience working in as a Frontend Engineer or comparable role.You won’t be a team of one though — you’ll be collaborating closely with other...</P>
                </CardBody>
              </div>
            </Card>
          ))}
      </Col>
      <Pagination />
    </Fragment>
  );
};

export default ListCard;
