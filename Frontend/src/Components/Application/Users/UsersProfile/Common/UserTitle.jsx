import React, { Fragment } from 'react';
import { Col, Row } from 'reactstrap';
import { H5, Image } from '../../../../../AbstractElements';
import { JOHANDIO } from '../../../../../Constant';

const UserTitle = () => {
    return (
        <Fragment>
            <Row>
                <Col sm="8">
                    <div className="media">
                        <Image attrImage={{ className: "img-thumbnail rounded-circle me-3", src: `${require("../../../../../assets/images/user/7.jpg")}`, alt: "Generic placeholder image" }} />
                        <div className="media-body align-self-center">
                            <H5 attrH5={{ className: "mt-0 user-name" }} >{JOHANDIO}</H5>
                        </div>
                    </div>
                </Col>
                <Col sm="4" className="align-self-center">
                    {/* <div className="float-sm-end"><small>{"10 Hours ago"}</small></div> */}
                </Col>
            </Row>
        </Fragment >
    )
}

export default UserTitle;