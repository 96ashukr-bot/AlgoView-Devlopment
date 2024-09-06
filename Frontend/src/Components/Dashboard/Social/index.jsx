import React, { Fragment } from 'react';
import { Col, Container, Row } from 'reactstrap';
import { Breadcrumbs } from '../../../AbstractElements';
import { SmallWidgetsData, SocialWidgetData } from '../../../Data/Social';

import AllCampaigns from './AllCampaigns';
import FacebookCampaign from './FacebookCampaign';
import FollowerGender from './FollowerGender';
import InstagramSubscription from './InstagramSubscription';
import MobileAppCard from './MobileAppCard';
import SmallWidgets from './SmallWidgets';
import SocialProfileCard from './SocialProfileCard';
import SocialWidget from '../../Common/CommonWidgets/SocialWidget';
import Views from './Views';

const Social = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle='Social' parent='Dashboard' title='Social' />
      <Container fluid={true}>
        <Row>
          <Col xxl='3' xl='4' className='col-ed-4 box-col-4'>
            <Row>
              <Col xl='12' md='6'>
                <SocialProfileCard />
              </Col>
              <Col xl='12' md='6'>
                <MobileAppCard />
              </Col>
            </Row>
          </Col>
          <Col xxl='6' xl='8' className='col-ed-8 box-col-8e'>
            <Row>
              {SocialWidgetData.map((item, i) => (
                <Col md='4' sm='6' key={i}>
                  <SocialWidget data={item} />
                </Col>
              ))}
              <Col md='8'>
                <InstagramSubscription />
              </Col>
              <Col md='4'>
                <Row>
                  {SmallWidgetsData.map((item, i) => (
                    <Col md='12' sm='6' key={i}>
                      <SmallWidgets data={item} />
                    </Col>
                  ))}
                </Row>
              </Col>
            </Row>
          </Col>
          <Col xl='3' className='col-ed-none d-xxl-block d-lg-none box-col-none'>
            <Row>
              <Col lg='12' sm='6'>
                <FollowerGender />
              </Col>
              <Col lg='12' sm='6'>
                <FacebookCampaign />
              </Col>
            </Row>
          </Col>
          <Col xl='7'>
            <AllCampaigns />
          </Col>
          <Col xl='5'>
            <Views />
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
};

export default Social;
