import React, { Fragment } from 'react';
import { X } from 'react-feather';
import { Card, CardBody, Col, Media, Row } from 'reactstrap';
import { Btn, H6 } from '../../../../AbstractElements';
import { CancelledOrders, Price } from '../../../../Constant';
import { OrderHistoryData } from '../../../../Data/Ecommerce/OrderHistoryList';
import HeaderCard from '../../../Common/Component/HeaderCard';

const CancelledOrdersClass = () => {
  return (
    <Fragment>
      <Col sm='12'>
        <Card>
          <HeaderCard title={CancelledOrders} />
          <CardBody>
            <Row className='g-sm-4 g-3'>
              {OrderHistoryData.map((items, i) => (
                <Col xxl='4' md='6' key={i}>
                  <div className='prooduct-details-box'>
                    <Media>
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
                        <Btn attrBtn={{ color: 'danger', size: 'xs' }}>Cancelled</Btn>
                        <X className='close' />
                      </div>
                    </Media>
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

export default CancelledOrdersClass;
