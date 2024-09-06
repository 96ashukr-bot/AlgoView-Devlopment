import { Btn, H5, H6 } from '../../../AbstractElements';
import { DetailesSidebarData } from '../../../Data/KnowledegesBase';
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
                                DetailesSidebarData.map((item) => {
                                    return (
                                        <Media key={item.id}>
                                            <Media body><span className="f-w-600">{item.title1}</span>
                                                <H6>{item.title2}<a href="#javascript">&nbsp;{item.title3}</a></H6>
                                                <span className="d-block">
                                                    <i className="fa fa-star font-warning"></i>
                                                    <i className="fa fa-star font-warning"></i>
                                                    <i className="fa fa-star font-warning"></i>
                                                    <i className="fa fa-star font-warning"></i>
                                                    <i className="fa fa-star-half-o font-warning"></i>
                                                </span>
                                            </Media>
                                            <div>
                                                <H5 attrH5={{ className: 'mb-0 p-0 font-primary' }}>{item.date}</H5><span className="d-block">{item.month}</span>
                                            </div>
                                        </Media>
                                    );
                                })
                            }
                        </CardBody>
                    </Collapse>
                </Card>
            </Col>
        </Fragment>
    );
};
export default Sidebar2;