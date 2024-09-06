import React, { Fragment } from 'react';
import { Row, Col } from 'reactstrap';
import LeftBar from './LeftBar';
import RightBar from './RightBar';
import NewUserClass from './Timeline/NewUserClass';
import NewUserClass2 from './Timeline/NewUserClass2';

const TimelineTab = () => {
    return (
        <Fragment>
            <Row>
                <Col xl="3 xl-40 box-col-4" lg="12" md="5">
                    <div className="default-according style-1 faq-accordion job-accordion" id="accordionoc4">
                        <Row>
                            <LeftBar />
                        </Row>
                    </div>
                </Col>
                <Col xl="6 xl-60 box-col-8" lg="12" md="7">
                    <Row>
                        <NewUserClass />
                        <NewUserClass2 />
                    </Row>
                </Col>
                <Col xl="3 xl-100 box-col-12">
                    <div className="default-according style-1 faq-accordion job-accordion" id="accordionoc1">
                        <Row>
                            <RightBar />
                        </Row>
                    </div>
                </Col>
            </Row>
        </Fragment>
    );
};

export default TimelineTab;