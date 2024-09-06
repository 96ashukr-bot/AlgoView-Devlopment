import React from "react";
import { Row, Col, CardBody } from 'reactstrap'
import { P, Ribbon } from '../../../AbstractElements';

const RibbonClass = () => {
    return (
        <CardBody>
            <Row>
                <Col sm="12" md="6" lg="4">
                    <div className="ribbon-wrapper">
                        <Ribbon attrRibbons={{ className: 'ribbon ribbon-primary ribbon-space-bottom' }} >Ribbon</Ribbon>
                        <P>Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text.</P>
                    </div>
                </Col>
                <Col sm="12" md="6" lg="4">
                    <div className="ribbon-wrapper">
                        <div className="ribbon ribbon-primary ribbon-space-bottom">Ribbon</div>
                        <P>Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text.</P>
                    </div>
                </Col>
                <Col sm="12" md="6" lg="4">
                    <div className="ribbon-wrapper">
                        <div className="ribbon ribbon-primary ribbon-space-bottom">Ribbon</div>
                        <P>Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text.</P>
                    </div>
                </Col>
            </Row>
        </CardBody>
    )
}

export default RibbonClass;