import React, { Fragment } from "react";
import { Card, CardBody, CardHeader, Col, Row } from "reactstrap";
import { H5, Image } from "../../../AbstractElements";
import { HoverEffect } from "../../../Constant";

const Hover11 = () => {
    return (
        <Fragment>
            <Row>
                <Col sm="12">
                    <Card>
                        <CardHeader>
                            <H5>{HoverEffect} <span className="digits">{"11"}</span></H5>
                        </CardHeader>
                        <CardBody>
                            <div id="aniimated-thumbnials10" className="row gallery my-gallery">
                                <figure itemProp="associatedMedia"
                                    className="col-md-3 col-6 img-hover hover-11">
                                    <div className="">
                                        <Image attrImage={{
                                            className: "img-fluid", src: `${require('../../../assets/images/lightgallry/08.jpg')}`, itemProp: "thumbnail",
                                            alt: ""
                                        }} />
                                    </div>
                                </figure>
                                <figure itemProp="associatedMedia"
                                    className="col-md-3 col-6 img-hover hover-11">
                                    <div className="">
                                        <Image attrImage={{
                                            className: "img-fluid", src: `${require('../../../assets/images/lightgallry/09.jpg')}`, itemProp: "thumbnail",
                                            alt: ""
                                        }} />
                                    </div>
                                </figure>
                                <figure itemProp="associatedMedia"
                                    className="col-md-3 col-6 img-hover hover-11">
                                    <div className="">
                                        <Image attrImage={{
                                            className: "img-fluid", src: `${require('../../../assets/images/lightgallry/010.jpg')}`, itemProp: "thumbnail",
                                            alt: ""
                                        }} />
                                    </div>
                                </figure>
                                <figure itemProp="associatedMedia"
                                    className="col-md-3 col-6 img-hover hover-11">
                                    <div className="">
                                        <Image attrImage={{
                                            className: "img-fluid", src: `${require('../../../assets/images/lightgallry/011.jpg')}`, itemProp: "thumbnail",
                                            alt: ""
                                        }} />
                                    </div>
                                </figure>
                            </div>
                        </CardBody>
                    </Card>
                </Col>
            </Row>
        </Fragment>
    )
}

export default Hover11;