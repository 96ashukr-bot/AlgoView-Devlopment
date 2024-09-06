import React, { Fragment } from 'react';
import { X } from 'react-feather';
import { Card, CardBody, CardHeader, Col, Row } from 'reactstrap';
import { H6, Btn } from '../../../../AbstractElements';
import { NewOrder, Price } from '../../../../Constant';
import { OrderHistoryData } from '../../../../Data/Ecommerce/OrderHistoryList';

const NewOrderClass = () => {
  return (
    <Fragment>
      <Col sm='12'>
        <Card>
          <CardHeader>
            <h5>{NewOrder}</h5>
          </CardHeader>
          <CardBody>
            <Row className='g-sm-4 g-3'>
              {OrderHistoryData.slice(0, 9).map((items, i) => (
                <Col xxl='4' md='6' key={i}>
                  <div className='prooduct-details-box'>
                    <div className='media'>
                      {items.Product}
                      <div className='media-body ms-3'>
                        <div className='product-name'>
                          <H6>{items.Product_Name}</H6>
                        </div>
                        <div className='rating'>
                          <i className='fa fa-star'></i>
                          <i className='fa fa-star'></i>
                          <i className='fa fa-star'></i>
                          <i className='fa fa-star'></i>
                          <i className='fa fa-star'></i>
                        </div>
                        <div className='price d-flex'>
                          <div className='text-muted me-2'>{Price}</div>: {items.Price}
                        </div>
                        <div className='avaiabilty'>
                          <div className='text-success'>{items.Stock}</div>
                        </div>
                        <Btn attrBtn={{ color: 'primary', size: 'xs' }}>Processing</Btn>
                        <X className='close' />
                      </div>
                    </div>
                  </div>
                </Col>
              ))}
            </Row>
          </CardBody>
        </Card>
      </Col>
    </Fragment>
  );
};

export default NewOrderClass;
