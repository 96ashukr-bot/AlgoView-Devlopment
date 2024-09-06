import React, { Fragment } from 'react';
import CardHeader from 'react-bootstrap/esm/CardHeader';
import { Link } from 'react-router-dom';
import { Card, CardBody, Col } from 'reactstrap';
import { H5, UL, LI, Image, P } from '../../../AbstractElements';
import { BlogMessage, Inprogress, PaperNoteTitle, ViewProject } from '../../../Constant';
import blogImage from '../../../assets/images/dashboard/papernote.jpg';
import { NoteLabels } from '../../../Data/DefaultDashboard';

const PaperNote = () => {
  return (
    <Col xxl='5' lg='8' md='11' className='box-col-8 col-ed-6'>
      <Card className=' papernote-wrap'>
        <CardHeader className=' card-no-border'>
          <div className='header-top'>
            <H5>{PaperNoteTitle}</H5>
            <Link className='f-light d-flex align-items-center' to='#'>
              {ViewProject} <i className='f-w-700 icon-arrow-top-right' />
            </Link>
          </div>
        </CardHeader>
        <CardBody className='pt-0'>
          <Image attrImage={{ className: 'banner-img img-fluid', src: blogImage, alt: 'multicolor background' }} />
          <div className='note-content mt-sm-4 mt-2'>
            <P>{BlogMessage}</P>
            <div className='note-labels'>
              <UL attrUL={{ horizontal: true }}>
                {NoteLabels.map((item, i) => (
                  <LI key={i}>
                    <span className={`badge badge-light-${item.color}`}>{item.title}</span>
                  </LI>
                ))}
              </UL>
              <div className='last-label'>
                <span className='badge badge-light-success'>{Inprogress}</span>
              </div>
            </div>
            <div className='mt-sm-4 mt-2 user-details'>
              <div className='customers'>
                <UL>
                  {[1, 6, 7, 3, 8, 5].map((item, i, arr) => (
                    <Fragment key={i}>
                      {i !== arr.length - 1 && (
                        <LI attrLI={{ className: 'd-inline-block' }}>
                          <Image attrImage={{ className: 'm-0 img-40 rounded-circle', src: require(`../../../assets/images/dashboard/user/${item}.jpg`), alt: 'user' }} />
                        </LI>
                      )}
                      {i === arr.length - 1 && (
                        <LI attrLI={{ className: 'd-inline-block' }}>
                          <div className='light-card'>
                            <span className='f-w-500'>+{item}</span>
                          </div>
                        </LI>
                      )}
                    </Fragment>
                  ))}
                </UL>
              </div>
              <div className='d-flex align-items-center'>
                <H5 attrH5={{ className: 'mb-0 font-primary f-18 me-1' }}>$239,098</H5>
                <span className='f-light f-w-500'>(Budget)</span>
              </div>
            </div>
          </div>
        </CardBody>
      </Card>
    </Col>
  );
};

export default PaperNote;
