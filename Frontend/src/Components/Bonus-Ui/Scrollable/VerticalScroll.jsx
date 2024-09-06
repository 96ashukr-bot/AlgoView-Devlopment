import React, { Fragment } from 'react';
import { Card, CardBody, Col } from 'reactstrap';
import { P } from '../../../AbstractElements';
import ScrollBars from 'react-custom-scrollbars-2';
import HeaderCard from '../../Common/Component/HeaderCard';
import { scrollpara, scrollpara1, scrollpara2, scrollpara3 } from '../../../Constant';

const VerticalScroll = () => {
    return (
        <Fragment>
            <Col sm="6">
                <Card>
                    <HeaderCard title="Vertical Scroll" />
                    <CardBody>
                        <ScrollBars className='vertical-scroll scroll-demo' style={{width: '100%',height:300}}>
                            <P>{scrollpara}</P>
                            <P>{scrollpara1}</P>
                            <P>{scrollpara2}</P>
                            <P>{scrollpara1}</P>
                            <P>{scrollpara3}</P>
                        </ScrollBars>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default VerticalScroll;