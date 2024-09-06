import { H4, H6, LI, P, UL, Image } from '../../../AbstractElements';
import imgg from '../../../assets/images/blog/blog.jpg';
import PagesSort from './Pages';
import axios from 'axios';
import React, { Fragment, useEffect, useState } from 'react';
import { Card, Col, Row } from 'reactstrap';
import { SearchAllTabsApi } from '../../../api';

const AllTabs = () => {
  const [tabsData, setTabsData] = useState('');
  useEffect(() => {
    axios.get(SearchAllTabsApi).then((resp) => {
      setTabsData(resp.data);
    });
  }, []);
  return (
    <Fragment>
      <div className='search-links tab-pane fade show active' id='all-links' role='tabpanel' aria-labelledby='all-link'>
        <Row>
          <Col xxl='8' xl='6' className='box-col-12'>
            <P attrPara={{ className: 'pb-4' }}>About 6,000 results (0.60 seconds)</P>
            {tabsData &&
              tabsData.map((item) => {
                return (
                  <div className='info-block' key={item.id}>
                    <a href='#javascript'>{item.url}</a>
                    <H6>{item.title}</H6>
                    <P>{item.detail}</P>
                    <div className='star-ratings'>
                      <UL attrUL={{ className: 'simple-list border-0 search-info' }}>
                        <LI attrLI={{ className: 'border-0' }}>
                          <i className='icofont icofont-ui-rating'></i>
                          <i className='icofont icofont-ui-rating'></i>
                          <i className='icofont icofont-ui-rating'></i>
                          <i className='icofont icofont-ui-rate-blank'></i>
                          <i className='icofont icofont-ui-rate-blank'></i>
                        </LI>
                        <LI attrLI={{ className: 'border-0' }}>{item.star}</LI>
                        <LI attrLI={{ className: 'border-0' }}>{item.vote}</LI>
                        <LI attrLI={{ className: 'border-0' }}>{item.news}</LI>
                      </UL>
                    </div>
                  </div>
                );
              })}
          </Col>
          <Col xxl='4' xl='6' className='box-col-12 mt-4'>
            <Card className='o-hidden'>
              <div className='blog-box blog-shadow'>
                <Image attrImage={{ className: 'img-fluid bg-img-cover', src: `${imgg}`, alt: '' }} />
                <div className='blog-details'>
                  <P attrPara={{ className: 'digits' }}>25 July 2022</P>
                  <H4>Accusamus et iusto odio dignissimos ducimus qui blanditiis.</H4>
                  <UL attrUL={{ className: 'simple-list border-0 blog-social digits d-flex flex-row' }}>
                    <LI attrLI={{ className: 'border-0' }}>
                      <i className='icofont icofont-user'></i>Mark Jecno
                    </LI>
                    <LI attrLI={{ className: 'border-0' }}>
                      <i className='icofont icofont-thumbs-up'></i>02 Hits
                    </LI>
                  </UL>
                </div>
              </div>
            </Card>
            {tabsData &&
              tabsData.slice(0, 2).map((item) => {
                return (
                  <div className='info-block' key={item.id}>
                    <a href='#javascript'>{item.url}</a>
                    <H6>{item.title}</H6>
                    <P>{item.detail}</P>
                    <div className='star-ratings'>
                      <UL attrUL={{ className: 'simple-list border-0 search-info' }}>
                        <LI attrLI={{ className: 'border-0' }}>
                          <i className='icofont icofont-ui-rating'></i>
                          <i className='icofont icofont-ui-rating'></i>
                          <i className='icofont icofont-ui-rating'></i>
                          <i className='i cofont icofont-ui-rate-blank'></i>
                          <i className='icofont icofont-ui-rate-blank'></i>
                        </LI>
                        <LI attrLI={{ className: 'border-0' }}>{item.star}</LI>
                        <LI attrLI={{ className: 'border-0' }}>{item.vote}</LI>
                        <LI attrLI={{ className: 'border-0' }}>{item.news}</LI>
                      </UL>
                    </div>
                  </div>
                );
              })}
          </Col>
          <Col xs='12'>
            <PagesSort />
          </Col>
        </Row>
      </div>
    </Fragment>
  );
};
export default AllTabs;
