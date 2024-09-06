import React, { Fragment } from "react";
import { Row, Col, Card, CardHeader, CardBody } from 'reactstrap'
import { Icons } from "../../../Constant";

const FontawesomeCommon = ({ iconType, title, parentCallback }) => {

    const getItag = (tag) => {
        parentCallback(tag)
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
                            {iconType.map((icon, i) => {
                                return (
                                    <Col sm="6" md="4" xl="3" key={i} onClick={(e) => getItag(icon)}>
                                        <i className={`fa fa-${icon}`}></i> {"fa fa-"}{icon}
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

export default FontawesomeCommon;