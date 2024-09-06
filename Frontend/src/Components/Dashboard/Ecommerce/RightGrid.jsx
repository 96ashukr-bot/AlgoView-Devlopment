import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { H5, UL, LI, P, H6, Image } from '../../../AbstractElements';
import { RecentActivity, TopCategoriesTitle } from '../../../Constant';
import { RecentActivityData } from '../../../Data/Ecommerce';
import TopCategories from './TopCategories';

const RightGrid = () => {
  return (
    <Col xxl='2' xl='3' md='4' className='grid-ed-none box-col-4e d-xxl-block d-none'>
      <Card>
        <CardHeader className='card-no-border'>
          <H5>{TopCategoriesTitle}</H5>
        </CardHeader>
        <CardBody className='card-body pt-0'>
          <TopCategories />
          <div className='recent-activity notification'>
            <H5>{RecentActivity}</H5>
            <UL>
              {RecentActivityData.map((item, i) => (
                <LI key={i} attrLI={{ className: 'd-flex' }}>
                  <div className={`activity-dot-${item.status}`} />
                  <div className='w-100 ms-3'>
                    <P attrPara={{ className: 'd-flex justify-content-between mb-2' }}>
                      <span className='date-content light-background'>{item.date}</span>
                    </P>
                    <H6 attrH6={{ className: 'm-0' }}>
                      {item.title}
                      <span className='dot-notification' />
                    </H6>
                    <span className='f-light'>{item.subTitle}</span>
                    {item.image && (
                      <div className='recent-images'>
                        <UL attrUL={{ horizontal: true }}>
                          {item.image.map((imageItem, i) => (
                            <LI key={i}>
                              <div className='recent-img-wrap'>
                                <Image attrImage={{ className: 'm-0', src: require(`../../../assets/images/dashboard-2/product/${imageItem}.png`), alt: 'chair' }} />
                              </div>
                            </LI>
                          ))}
                        </UL>
                      </div>
                    )}
                  </div>
                </LI>
              ))}
            </UL>
          </div>
        </CardBody>
      </Card>
    </Col>
  );
};

export default RightGrid;
