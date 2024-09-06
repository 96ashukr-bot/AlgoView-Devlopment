import React, { Fragment } from 'react';
import Scrollbars from 'react-custom-scrollbars-2';
import { Card, CardBody, Col } from 'reactstrap';
import { Image } from '../../../AbstractElements';
import { bothSidescroll } from '../../../Constant';
import HeaderCard from '../../Common/Component/HeaderCard';

const BothSideScroll = () => {
  return (
    <Fragment>
      <Col sm='6'>
        <Card>
          <HeaderCard title={bothSidescroll} />
          <CardBody>
            <div className='scroll-bar-wrap'>
              <Scrollbars className='both-side-scroll scroll-demo p-0' style={{ width: '100%', height: 300 }}>
                <Image attrImage={{ src: `${require('../../../assets/images/banner/1.jpg')}`, alt: '', width: '800', height: '600' }} />
              </Scrollbars>
            </div>
          </CardBody>
        </Card>
      </Col>
    </Fragment>
  );
};

export default BothSideScroll;
