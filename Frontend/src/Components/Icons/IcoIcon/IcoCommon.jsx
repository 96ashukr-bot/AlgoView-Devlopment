import React, { Fragment } from "react";
import { Row, Col, Card, CardHeader, CardBody } from 'reactstrap'
import { Icons } from "../../../Constant";

const IcoCommon = ({ title, iconType, parentCallback }) => {

    const getItag = (tag) => {
        parentCallback(tag);
    }

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <h5 className="m-b-0"><span className="digits">{title}</span> {Icons}</h5>
                    </CardHeader>
                    <CardBody>
                        <Row className="icon-lists">
                            {iconType.map((iconItem, i) => {
                                return (
                                    <Col sm="6" lg="4" key={i}
                                        onClick={() => {
                                            getItag(iconItem);

                                        }}
                                    >
                                        <i className={`icofont icofont-${iconItem}`}></i> {iconItem}
                                    </Col>
                                )
                            })
                            }
                        </Row>
                    </CardBody>
                </Card>
            </Col>

        </Fragment>
    )
}

export default IcoCommon;