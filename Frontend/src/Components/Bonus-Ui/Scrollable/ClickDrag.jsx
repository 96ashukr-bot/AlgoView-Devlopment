import React, { Fragment } from 'react';
import { Card, CardBody, Col } from 'reactstrap';
import { Image } from '../../../AbstractElements';
import { Scrollbars } from 'react-custom-scrollbars-2';
import HeaderCard from '../../Common/Component/HeaderCard';
import { clickAndDrag } from '../../../Constant';

const ClickAndDrag = () => {
    return (
        <Fragment>
            <Col sm="6">
                <Card>
                    <HeaderCard title={clickAndDrag} />
                    <CardBody>
                        <div className="scroll-bar-wrap">
                            <Scrollbars className='click-drag-handler scroll-demo p-0' style={{width: '100%',height:300}}>
                                <Image attrImage={{ src: require('../../../assets/images/banner/2.jpg'), alt: '', width: '100%', height: '600' }} />
                            </Scrollbars>
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default ClickAndDrag;