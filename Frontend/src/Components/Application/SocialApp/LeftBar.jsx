import React, { Fragment } from 'react';
import { Col, Card } from 'reactstrap';
import timeline3 from "../../../assets/images/social-app/timeline-3.png";
import { Image } from '../../../AbstractElements';
import MyProfileClass from './Leftbar/MyProfileClass';
import MutualFriendsClass from './Leftbar/MutualFriendsClass';
import ActivityFeedClass from './Leftbar/ActivityFeedClass';


const LeftBar = () => {

    return (
        <Fragment>
            <Col xl="12">
                <MyProfileClass />
            </Col>
            <Col xl="12">
                <Card><Image attrImage={{ className: "img-fluid", alt: "", src: `${timeline3}` }} /></Card>
            </Col>
            <Col xl="12">
                <MutualFriendsClass />
            </Col>
            <Col xl="12">
                <ActivityFeedClass />
            </Col>
        </Fragment>
    );
};

export default LeftBar;