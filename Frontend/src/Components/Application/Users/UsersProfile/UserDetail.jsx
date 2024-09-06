import React, { Fragment } from 'react';
import { Col, Card } from 'reactstrap';
import { Image, P } from '../../../../AbstractElements';
import { UserProfileDesc1 } from '../../../../Constant';
import UserFooter from './Common/UserFooter';
import UserTitle from './Common/UserTitle';

const UserDetails = () => {
    return (
        <Fragment>
            <Col sm="12" >
                <Card className="step5" data-intro="This is the your first Post">
                    <div className="profile-img-style">
                        <UserTitle />
                        <hr />
                        <P>{UserProfileDesc1}</P>
                        <div className="img-container">
                            <div id="aniimated-thumbnials">
                                <a href="#javascript">
                                    <Image attrImage={{ className: "img-fluid rounded", src: `${require("../../../../assets/images/other-images/profile-style-img3.png")}`, alt: "gallery" }} />
                                </a>
                            </div>
                        </div>
                        <UserFooter />
                    </div>
                </Card>
            </Col>
        </Fragment>
    )
}

export default UserDetails;