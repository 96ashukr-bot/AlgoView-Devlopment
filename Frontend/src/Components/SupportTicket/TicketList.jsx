import { Profit, Loss } from '../../Constant';
import { TicketData } from '../../Data/SupportTicket';
import { H4, H6, LI, UL } from '../../AbstractElements';
import React, { Fragment } from 'react';
import { Row, Col, Card, CardBody } from 'reactstrap';
import CountUp from 'react-countup';

const TicketList = () => {
  return (
    <Fragment>
      <Row>
        {TicketData.map((item) => {
          return (
            <Col xl='4' sm='6' key={item.id}>
              <Card className='ecommerce-widget pro-gress'>
                <CardBody className='support-ticket-font'>
                  <Row>
                    <Col xs='5'>
                      <H6>{item.title}</H6>
                      <H4 attrH4={{ className: 'total-num counter' }}>
                        <CountUp end={item.num} duration={5} />
                      </H4>
                    </Col>
                    <Col xs='7'>
                      <div className='text-md-end'>
                        <UL attrUL={{ className: 'border-0 simple-list' }}>
                          <LI attrLI={{ className: 'border-0' }}>
                            {Profit}
                            <span className='product-stts txt-primary ms-2'>
                              {'8989'}
                              <i className='icon-angle-up f-12 ms-1'></i>
                            </span>
                          </LI>
                          <LI attrLI={{ className: 'border-0' }}>
                            {Loss}
                            <span className='product-stts txt-danger ms-2'>
                              {'2560'}
                              <i className='icon-angle-down f-12 ms-1'></i>
                            </span>
                          </LI>
                        </UL>
                      </div>
                    </Col>
                  </Row>
                  <div className='progress-showcase'>
                    <div className='progress sm-progress-bar'>
                      <div className={item.class} role='progressbar' style={{ width: '70%' }} aria-valuenow='25' aria-valuemin='0' aria-valuemax='100'></div>
                    </div>
                  </div>
                </CardBody>
              </Card>
            </Col>
          );
        })}
      </Row>
    </Fragment>
  );
};
export default TicketList;
