import React, { Fragment } from 'react';
import { Col, Card, Row } from 'reactstrap';
import { Image, P } from '../../../../AbstractElements';
import { UserProfileDesc3 } from '../../../../Constant';
import UserFooter from './Common/UserFooter';
import UserTitle from './Common/UserTitle';

const UserDetails4 = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <div className="profile-img-style">
                        <UserTitle />
                        <hr />
                        <Row>
                            <Col lg="12" xl="4 box-col-5">
                                <div id="aniimated-thumbnials-3">
                                    <a href="#javascript">
                                        <Image attrImage={{ className: "img-fluid rounded", src: `${require("../../../../assets/images/blog/img.png")}`, alt: "gallery" }} /></a></div>
                                <UserFooter />
                            </Col>
                            <Col xl="6 box-col-7">
                                <P>{UserProfileDesc3}</P>
                            </Col>
                        </Row>
                    </div>
                </Card>
            </Col>

        </Fragment>
    )
}

export default UserDetails4;