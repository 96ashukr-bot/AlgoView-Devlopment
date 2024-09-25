import { Btn, H5, H6 } from '../../../AbstractElements';
// import { DetailesSidebarData } from '../../../Data/KnowledegesBase';
import React, { Fragment, useState } from 'react';
import { Card, CardBody, CardHeader, Col, Collapse, Media } from 'reactstrap';

const Sidebar2 = () => {
    const [isProfile, setisProfile] = useState(true);
    return (
        <Fragment>
            <Col xl="12">
                <Card>
                    <CardHeader>
                        <H5 attrH5={{ className: 'mb-0 p-0' }}>
                            <Btn attrBtn={{ color: 'link ps-0', onClick: () => setisProfile(!isProfile) }} >Upcoming Courses</Btn>
                        </H5>
                    </CardHeader>
                    <Collapse isOpen={isProfile}>
                        <CardBody className="upcoming-course">
                            {

                            }
                        </CardBody>
                    </Collapse>
                </Card>
            </Col>
        </Fragment>
    );
};
export default Sidebar2;