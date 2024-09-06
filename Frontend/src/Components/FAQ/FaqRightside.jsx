import React, { Fragment } from 'react';
import { Row, Col, Card, CardBody, CardHeader, Media, Input } from 'reactstrap';
import { SearchArticles, Navigation, AskOurCommunity, AskQuestion, ContactUs, LatestUpdates, SeeAll } from '../../Constant';
import { Search, MessageCircle, Mail, HelpCircle, Settings, MessageSquare } from 'react-feather';
import { H5, LI, P, UL } from '../../AbstractElements';
import { ASKQUESData, LatestData } from '../../Data/FAQ';

const FaqRightsidebae = () => {
  return (
    <Fragment>
      <Col xl='4' lg='6' md='5' className='xl-40 box-col-4'>
        <Row>
          <Col lg='12'>
            <div className='card card-mb-faq xs-mt-search'>
              <CardHeader className='faq-header'>
                <H5>{SearchArticles}</H5>
                <HelpCircle />
              </CardHeader>
              <CardBody className='faq-body'>
                <div className='faq-form'>
                  <Input className='form-control' type='text' placeholder='Search..' />
                  <Search className='search-icon' />
                </div>
              </CardBody>
            </div>
          </Col>
          <Col lg='12'>
            <Card className='card-mb-faq'>
              <CardHeader className='faq-header'>
                <H5>{Navigation}</H5>
                <Settings />
              </CardHeader>
              <CardBody className='faq-body'>
                <div className='navigation-btn'>
                  <a className='btn btn-primary' style={{ color: '#fff' }} href='#javascript'>
                    <MessageSquare className='m-r-10' />
                    {AskQuestion}
                  </a>
                </div>
                <div className='navigation-option'>
                  <UL attrUL={{ className: 'simple-list border-0' }}>
                    {ASKQUESData.map((item, i) => {
                      return (
                        <LI attrLI={{ className: 'border-0' }} key={i}>
                          <a href='#javascript'>
                            {item.icon}
                            {item.title}
                          </a>
                          <span className={item.class}>{item.val}</span>
                        </LI>
                      );
                    })}
                  </UL>
                  <hr />
                  <UL>
                    <LI>
                      <a href='#javascript'>
                        <MessageCircle />
                        {AskOurCommunity}
                      </a>
                    </LI>
                    <LI>
                      <a href='#javascript'>
                        <Mail />
                        {ContactUs}
                      </a>
                    </LI>
                  </UL>
                </div>
              </CardBody>
            </Card>
          </Col>
          <Col lg='12'>
            <Card>
              <CardHeader className='faq-header'>
                <H5 attrH5={{ className: 'd-inline-block' }}>{LatestUpdates}</H5>
                <span className='pull-right d-inline-block'>{SeeAll}</span>
              </CardHeader>
              <CardBody className='faq-body'>
                {LatestData.map((item, i) => {
                  return (
                    <Media className='updates-faq-main' key={i}>
                      <div className='updates-faq'>{item.Iconclass}</div>
                      <Media body className='updates-bottom-time'>
                        <P>
                          {item.name} <a href='#javascript'>{item.val}</a> {item.title}
                        </P>
                        <P>{item.time}</P>
                      </Media>
                    </Media>
                  );
                })}
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Col>
    </Fragment>
  );
};
export default FaqRightsidebae;
