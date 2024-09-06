import React, { Fragment } from 'react';
import { Card, Col } from 'reactstrap';
import HeaderCard from '../../../Common/Component/HeaderCard';
import PeopleKnows from './PeopleKnows';

const AvatarShowcase = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <HeaderCard title={"Viewed Your Profile"} />
                    <PeopleKnows />
                </Card>
            </Col>
        </Fragment>
    )
}

export default AvatarShowcase;