import React, { Fragment } from 'react';
import { Row, Col, Card, CardBody, Media, Form, Label, Input } from 'reactstrap';
import { H6, P } from '../../../../AbstractElements';
import { COD, Fast, NoBorder } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';
import FooterCard from '../Common/FooterCard';

const NoBorderClass = () => {
  return (
    <Fragment>
      <Col sm='12' xxl='6' className='box-col-12'>
        <Card>
          <HeaderCard title={NoBorder} span1='By adding .plain-style class to .mega-inline You can archive this style' />
          <CardBody>
            <Form className='mega-inline plain-style'>
              <Row>
                <Col sm='6'>
                  <Card>
                    <Media className='p-20'>
                      <div className='radio radio-primary me-3'>
                        <Input id='radio11' type='radio' name='radio1' value='option1' />
                        <Label for='radio11'></Label>
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
                      <div className='radio radio-secondary me-3'>
                        <Input id='radio12' type='radio' name='radio1' value='option1' />
                        <Label for='radio12'></Label>
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

export default NoBorderClass;
