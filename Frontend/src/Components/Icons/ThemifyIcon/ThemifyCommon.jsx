import React, { Fragment } from "react";
import { Icons } from "../../../Constant";
import { Row, Col, Card, CardHeader, CardBody } from 'reactstrap'

const ThemifyCommon = ({ iconType, title, parentCallback }) => {

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
                                    <Col sm="6" lg="4" key={i} onClick={(e) => getItag(icon)}>
                                        <i className={`${icon}`}></i> {icon}
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

export default ThemifyCommon;