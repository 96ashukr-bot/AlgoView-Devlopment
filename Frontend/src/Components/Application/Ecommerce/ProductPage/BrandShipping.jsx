import React, { Fragment } from 'react';
import { H4, H5, LI, P, UL } from '../../../../AbstractElements';
import { Clock, CreditCard, Gift, Truck } from 'react-feather';
import { Card, CardBody } from 'reactstrap';

const BrandShipping = () => {
  return (
    <Fragment>
      <Card>
        <CardBody>
          <div className='filter-block'>
            <H4>{'Brand'}</H4>
            <UL>
              <LI attrLI={{ className: 'border-0' }}>{'Clothing'}</LI>
              <LI attrLI={{ className: 'border-0' }}>{'Bags'}</LI>
              <LI attrLI={{ className: 'border-0' }}>{'Footwear'}</LI>
              <LI attrLI={{ className: 'border-0' }}>{'Watches'}</LI>
              <LI attrLI={{ className: 'border-0' }}>{'ACCESSORIES'}</LI>
            </UL>
          </div>
        </CardBody>
      </Card>
      <Card>
        <CardBody>
          <div className='collection-filter-block'>
            <UL attrUL={{ className: 'pro-services' }}>
              <LI attrLI={{ className: 'border-0' }}>
                <div className='media'>
                  <Truck />
                  <div className='media-body'>
                    <H5>{'Free Shipping'}</H5>
                    <P>{'Free Shipping World Wide'}</P>
                  </div>
                </div>
              </LI>
              <LI attrLI={{ className: 'border-0' }}>
                <div className='media'>
                  <Clock />
                  <div className='media-body'>
                    <H5>{'24 X 7 Service'}</H5>
                    <P>{'Online Service For New Customer'}</P>
                  </div>
                </div>
              </LI>
              <LI attrLI={{ className: 'border-0' }}>
                <div className='media'>
                  <Gift />
                  <div className='media-body'>
                    <H5>{'Festival Offer'}</H5>
                    <P>{'New Online Special Festival'}</P>
                  </div>
                </div>
              </LI>
              <LI attrLI={{ className: 'border-0' }}>
                <div className='media'>
                  <CreditCard />
                  <div className='media-body'>
                    <H5>{'Online Payment'}</H5>
                    <P>{'Contrary To Popular Belief.'}</P>
                  </div>
                </div>
              </LI>
            </UL>
          </div>
        </CardBody>
      </Card>
    </Fragment>
  );
};
export default BrandShipping;
