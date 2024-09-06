import React from 'react';
import { Fragment } from 'react';
import { Breadcrumbs, H5 } from '../../../../AbstractElements';
import { Card, CardBody, CardHeader, Col, Container, Row } from 'reactstrap';
import DateRangedata from './DateRangedata';
import SingleDate from './SingleDate';
import TimeAndDate from './TimeAndDate';

const FormDateRangepickerContain = () => {
    return (
        <Fragment>
            <Breadcrumbs parent="Forms" title="Date Range Picker" subParent='Form Widgets' mainTitle="Date Range Picker" />
            <Container fluid={true}>
                <Row>
                    <Col>
                        <Card>
                            <CardHeader>
                                <H5>Date Range Picker</H5>
                            </CardHeader>
                            <CardBody>
                                <Row className="date-range-picker">
                                    <DateRangedata />
                                    <SingleDate />
                                    <TimeAndDate />
                                </Row>
                            </CardBody>
                        </Card>
                    </Col>
                </Row>
            </Container>
        </Fragment>
    );
};
export default FormDateRangepickerContain;