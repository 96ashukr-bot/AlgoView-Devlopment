import React, { Fragment } from 'react';
import { Row, Col, Card, CardHeader, CardBody, Media, Form, Label, Input, CardFooter } from 'reactstrap';
import { H5, H6, P, Btn } from '../../../../AbstractElements';
import { COD, Fast, HorizontalStyle, XYZSeller, ABCSeller, DeliveryOption, BuyingOption } from '../../../../Constant';
import { Submit, Cancel } from '../../../../Constant';

const HorizontalClass = () => {
  return (
    <Fragment>
      <Col sm='12' xxl='6' className='box-col-12'>
        <Card className='height-equal'>
          <CardHeader>
            <H5>{HorizontalStyle}</H5>
            <span>
              {'For Create inline megaoption add'} <code>{'.mega-horizontal'}</code> {'class in form tag'}
            </span>
          </CardHeader>
          <CardBody>
            <Form className='mega-horizontal'>
              <Row>
                <Col sm='3'>
                  <P attrPara={{ className: 'mega-title' }}>{DeliveryOption}</P>
                </Col>
                <Col sm='9'>
                  <Card>
                    <Media className='p-20'>
                      <div className='radio radio-primary me-3'>
                        <Input id='radio30' type='radio' name='radio1' value='option1' />
                        <Label for='radio30'></Label>
                      </div>
                      <Media body>
                        <H6 attrH6={{ className: 'mt-0 mega-title-badge' }}>
                          {COD}
                          <span className='badge badge-primary pull-right digits'>{'50 INR'}</span>
                        </H6>
                        <P>{'Estimated 5 Day Shipping ( Duties end tax may be due delivery )'}</P>
                      </Media>
                    </Media>
                  </Card>
                </Col>
                <Col sm='9 offset-sm-3'>
                  <Card>
                    <Media className='p-20'>
                      <div className='radio radio-secondary me-3'>
                        <Input id='radio31' type='radio' name='radio1' value='option1' />
                        <Label for='radio31'></Label>
                      </div>
                      <Media body>
                        <H6 attrH6={{ className: 'mt-0 mega-title-badge' }}>
                          {Fast} <span className='badge badge-secondary pull-right digits'>{'100 INR'}</span>
                        </H6>
                        <P>{'Estimated 1 Day Shipping ( Duties end tax may be due delivery )'}</P>
                      </Media>
                    </Media>
                  </Card>
                </Col>
                <Col sm='3'>
                  <P attrPara={{ className: 'mega-title' }}>{BuyingOption}</P>
                </Col>
                <Col sm='9'>
                  <Card>
                    <Media className='p-20'>
                      <div className='radio radio-success me-3'>
                        <Input id='radio32' type='radio' name='radio1' value='option1' />
                        <Label for='radio32'></Label>
                      </div>
                      <Media body>
                        <H6 attrH6={{ className: 'mt-0 mega-title-badge' }}>
                          {XYZSeller}
                          <span className='badge badge-success pull-right digits'>{'250 INR'}</span>
                        </H6>
                        <P attrPara={{ className: 'rating-star-wrapper' }}>
                          <i className='icofont icofont-star txt-warning'></i>
                          <i className='icofont icofont-star txt-warning'></i>
                          <i className='icofont icofont-star txt-warning'></i>
                          <i className='icofont icofont-star txt-warning'></i>
                          <i className='icofont icofont-star txt-warning m-r-5'></i>
                          {'5 start rating'}
                        </P>
                      </Media>
                    </Media>
                  </Card>
                </Col>
                <Col sm='9 offset-sm-3'>
                  <div className='card mb-0'>
                    <Media className='p-20'>
                      <div className='radio radio-info me-3'>
                        <Input id='radio33' type='radio' name='radio1' value='option1' />
                        <Label for='radio33'></Label>
                      </div>
                      <Media body>
                        <H6 attrH6={{ className: 'mt-0 mega-title-badge' }}>
                          {ABCSeller}
                          <span className='badge badge-info pull-right digits'>{'150 INR'}</span>
                        </H6>
                        <P attrH6={{ className: 'rating-star-wrapper' }}>
                          <i className='icofont icofont-star txt-warning'></i>
                          <i className='icofont icofont-star'></i>
                          <i className='icofont icofont-star'></i>
                          <i className='icofont icofont-star'></i>
                          <i className='icofont icofont-star m-r-5'></i>
                          {'1 start rating'}
                        </P>
                      </Media>
                    </Media>
                  </div>
                </Col>
              </Row>
            </Form>
          </CardBody>
          <CardFooter className='text-end'>
            <Btn attrBtn={{ color: 'primary', className: 'm-r-15 d-inline-flex', type: 'submit' }}>{Submit}</Btn>
            <Btn attrBtn={{ color: 'light', className: 'd-inline-flex', type: 'submit' }}>{Cancel}</Btn>
          </CardFooter>
        </Card>
      </Col>
    </Fragment>
  );
};

export default HorizontalClass;
