import React, { Fragment } from 'react';
import { Col, Card, Row } from 'reactstrap';
import { Image, P } from '../../../../AbstractElements';
import { UserProfileDesc1 } from '../../../../Constant';
import UserFooter from './Common/UserFooter';
import UserTitle from './Common/UserTitle';

const UserDetails2 = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <div className="profile-img-style">
                        <UserTitle />
                        <hr />
                        <P>{UserProfileDesc1}</P>
                        <Row className="mt-4 pictures">
                            <a className="col-sm-6" href="#javascript">
                                <Image attrImage={{ className: "img-fluid rounded", src: `${require("../../../../assets/images/other-images/profile-style-img.png")}`, alt: "gallery" }} />
                            </a>
                            <a className="col-sm-6" href="#javascript">
                                <Image attrImage={{ className: "img-fluid rounded", src: `${require("../../../../assets/images/other-images/profile-style-img.png")}`, alt: "gallery" }} />
                            </a>
                        </Row>
                        <UserFooter />
                    </div>
                </Card>
            </Col>

        </Fragment>
    )
}

export default UserDetails2;