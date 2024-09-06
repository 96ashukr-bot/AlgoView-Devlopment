import React, { Fragment } from 'react';
import { Row, Col, Card, CardBody, Media, Form, Label, Input } from 'reactstrap';
import { H6, P } from '../../../../AbstractElements';
import { COD, Fast, SolidBorderStyle } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';
import FooterCard from '../Common/FooterCard';

const SolidBorderClass = () => {
  return (
    <Fragment>
      <Col sm='12' xxl='6' className='box-col-12'>
        <Card>
          <HeaderCard title={SolidBorderStyle} span1='By adding .border-style class to .mega-inline You can archive this style' />
          <CardBody className='megaoptions-border-space-sm'>
            <Form className='mega-inline border-style'>
              <Row>
                <Col sm='6'>
                  <Card>
                    <Media className='p-20'>
                      <div className='radio radio-primary me-3'>
                        <Input id='radio15' type='radio' name='radio1' value='option1' />
                        <Label for='radio15'></Label>
                      </div>
                      <Media body>
                        <H6 attrH6={{ className: 'mt-0 mega-title-badge' }}>
                          {COD}
                          <span className='badge badge-primary pull-right digits'>{'50 INR'}</span>
                        </H6>
                        <P>{'Estimated 1 Day Shipping ( Duties end tax may be due delivery )'}</P>
                      </Media>
                    </Media>
                  </Card>
                </Col>
                <Col sm='6'>
                  <Card>
                    <Media className='p-20'>
                      <div className='radio radio-primary me-3'>
                        <Input id='radio16' type='radio' name='radio1' value='option1' />
                        <Label for='radio16'></Label>
                      </div>
                      <Media body>
                        <H6 attrH6={{ className: 'mt-0 mega-title-badge' }}>
                          {Fast}
                          <span className='badge badge-secondary pull-right digits'>{'100 INR'}</span>
                        </H6>
                        <P>{'Estimated 1 Day Shipping ( Duties end tax may be due delivery )'}</P>
                      </Media>
                    </Media>
                  </Card>
                </Col>
              </Row>
            </Form>
          </CardBody>
          <FooterCard />
        </Card>
      </Col>
    </Fragment>
  );
};

export default SolidBorderClass;
