import React, { Fragment } from 'react';
import Scrollbars from 'react-custom-scrollbars-2';
import { Card, CardBody, Col } from 'reactstrap';
import { Image } from '../../../AbstractElements';
import { smallSizescroll } from '../../../Constant';
import HeaderCard from '../../Common/Component/HeaderCard';

const SmallSizeScroll = () => {
    return (
        <Fragment>
            <Col sm="6">
                <Card>
                    <HeaderCard title={smallSizescroll} />
                    <CardBody>
                        <div className="scroll-bar-wrap">
                            <Scrollbars className='scrollbar-margins large-margin scroll-demo p-0' style={{height:300,width:'100%'}}>
                                <Image attrImage={{ src: `${require('../../../assets/images/banner/3.jpg')}`, alt: '', width: '735', height: '600' }} />
                            </Scrollbars>
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    ); 
};

export default SmallSizeScroll;