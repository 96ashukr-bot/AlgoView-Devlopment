import React, { Fragment } from 'react';
import { Col, Container, Row } from 'reactstrap';
import { Breadcrumbs } from '../../../AbstractElements';
import { CurrenciesWidgets, RadialProgressWidgetDataWidgetPage } from '../../../Data/Crypto';
import { Widgets2Data2Widgets, Widgets2DataWidgets, WidgetsData1WidgetsPage } from '../../../Data/DefaultDashboard';
import { SmallWidgetsData } from '../../../Data/Ecommerce';
import { CourseBoxData } from '../../../Data/OnlineCourse';
import { SocialWidgetDataWidgetPage } from '../../../Data/Social';

import CourseBox from '../../Common/CommonWidgets/CourseBox';
import CurrencyWidget from '../../Common/CommonWidgets/CurrencyWidget';
import RadialProgressWidget from '../../Common/CommonWidgets/RadialProgressWidget';
import SmallWidgets from '../../Common/CommonWidgets/SmallWidgets';
import SocialWidget from '../../Common/CommonWidgets/SocialWidget';
import Widgets1 from '../../Common/CommonWidgets/Widgets1';
import Widgets2 from '../../Common/CommonWidgets/Widgets2';
import YourBalanceCard from '../../Common/CommonWidgets/YourBalanceCard';

import FollowerGrowth from './FollowerGrowth';
import TotalUser from './TotalUser';
import VisitorsCard from './VisitorsCard';
import Calender from '../../Common/CommonWidgets/Calender';

const GeneralComponent = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle='General' parent='Widgets' title='General' />
      <Container fluid={true} className='general-widget'>
        <Row>
          {CurrenciesWidgets.map((item, i) => (
            <Col key={i} sm='4' xxl='2'>
              <CurrencyWidget mainClass='widget-currency' data={item} />
            </Col>
          ))}
          {RadialProgressWidgetDataWidgetPage.map((item, i) => (
            <Col xxl='3' sm='6' key={i}>
              <RadialProgressWidget chartHeight={130} data={item} />
            </Col>
          ))}
          {WidgetsData1WidgetsPage.map((item, i) => (
            <Col key={i} sm='6' xl='3' lg='6' className='box-col-6'>
              <Widgets1 data={item} />
            </Col>
          ))}
          <Col xxl='3' xl='4' md='6' className='box-col-6'>
            <Row>
              {CourseBoxData.map((item, i) => (
                <Col sm='12' key={i}>
                  <CourseBox mainClass='widget-course' data={item} />
                </Col>
              ))}
            </Row>
          </Col>
          <Col xxl='4' xl='5' md='6' className='box-col-6'>
            <Row>
              <Col xl='12'>
                <TotalUser />
              </Col>
              <Col xl='12'>
                <FollowerGrowth />
              </Col>
            </Row>
          </Col>
          <Col xxl='5' xl='3' md='12' className='box-col-12'>
            <VisitorsCard />
          </Col>
          {SocialWidgetDataWidgetPage.map((item, i) => (
            <Col xl='3' sm='6' key={i}>
              <SocialWidget data={item} />
            </Col>
          ))}
          <Col xxl='5' xl='8' className='box-col-12'>
            <Row className='g-sm-3 height-equal-2 widget-charts'>
              {SmallWidgetsData.map((data, i) => (
                <Col sm='6' key={i}>
                  <SmallWidgets mainClass='mb-sm-0' data={data} />
                </Col>
              ))}
              <Col sm='6'>
                <Widgets2 data={Widgets2DataWidgets} />
              </Col>
              <Col sm='6'>
                <Widgets2 chartClass='profit-chart' data={Widgets2Data2Widgets} />
              </Col>
            </Row>
          </Col>
          <Col xxl='3' xl='4' sm='6' className='box-col-6'>
            <YourBalanceCard />
          </Col>
          <Col xl='4' sm='6' className='d-xxl-block d-xl-none box-col-6'>
            <Calender />
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
};

export default GeneralComponent;
