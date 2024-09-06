import { H6, LI, P, UL } from '../../../AbstractElements';
import PagesSort from './Pages';
import axios from 'axios';
import React, { Fragment, useEffect, useState } from 'react';
import { Col, Media, Row } from 'reactstrap';
import { SearchAllTabsApi } from '../../../api';

const VideoTabs = () => {
  const [tabsDatas, setTabsDatas] = useState('');
  useEffect(() => {
    axios.get(SearchAllTabsApi).then((resp) => {
      setTabsDatas(resp.data);
    });
  }, []);
  return (
    <Fragment>
      <Row>
        <Col xl='6' className='xl-100 box-col-12'>
          <P attrPara={{ className: 'pb-4' }}>About 6,000 results (0.60 seconds)</P>
          {tabsDatas &&
            tabsDatas.map((item) => {
              return (
                <Media className='info-block' key={item.id}>
                  <iframe className='me-3 mb-3' title='1' width='200' height='100' src={item.videoLink}></iframe>
                  <Media body>
                    <H6>{item.title}</H6>
                    <a href='#javascript'>{item.url}</a>
                    <P>{item.detail}</P>
                    <div className='star-ratings'>
                      <UL attrUL={{ className: 'simple-list border-0 search-info' }}>
                        <LI attrLI={{ className: 'border-0' }}>{item.star}</LI>
                        <LI attrLI={{ className: 'border-0' }}>{item.vote}</LI>
                        <LI attrLI={{ className: 'border-0' }}>{item.news}</LI>
                      </UL>
                    </div>
                  </Media>
                </Media>
              );
            })}
        </Col>
        <Col xl='6' className='xl-100 box-col-12'>
          <P attrPara={{ className: 'pb-4' }}>About 6,000 results (0.60 seconds)</P>
          {tabsDatas &&
            tabsDatas.map((item) => {
              return (
                <Media className='info-block' key={item.id}>
                  <iframe className='me-3 mb-3' title='1' width='200' height='100' src={item.videoLink}></iframe>
                  <Media body>
                    <H6>{item.title}</H6>
                    <a href='#javascript'>{item.url}</a>
                    <P>{item.detail}</P>
                    <div className='star-ratings'>
                      <UL attrUL={{ className: 'simple-list border-0 search-info' }}>
                        <LI attrLI={{ className: 'border-0' }}>{item.star}</LI>
                        <LI attrLI={{ className: 'border-0' }}>{item.vote}</LI>
                        <LI attrLI={{ className: 'border-0' }}>{item.news}</LI>
                      </UL>
                    </div>
                  </Media>
                </Media>
              );
            })}
        </Col>
        <Col xs='12'>
          <PagesSort />
        </Col>
      </Row>
    </Fragment>
  );
};
export default VideoTabs;
