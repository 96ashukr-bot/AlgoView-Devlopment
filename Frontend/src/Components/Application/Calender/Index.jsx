import { BasicCalendars } from '../../../Constant';
import { Breadcrumbs } from '../../../AbstractElements';
import myEventsList from './Events';
import React, { Fragment } from 'react';
import { Card, CardBody, Col, Container, Row } from 'reactstrap';
import { Calendar, momentLocalizer, Views } from 'react-big-calendar';
import moment from 'moment';
import HeaderCard from '../../Common/Component/HeaderCard';

const localizer = momentLocalizer(moment);
let allViews = Object.keys(Views).map(k => Views[k]);

const CalenderContain = () => {
    return (
        <Fragment>
            <Breadcrumbs mainTitle="Calender" parent="Apps" title="Calender" />
            <Container fluid={true}>
                <Row>
                    <Col sm="12">
                        <Card>
                            <HeaderCard title={BasicCalendars} />
                            <CardBody>
                                <Calendar
                                    localizer={localizer}
                                    scrollToTime={new Date(1970, 1, 1, 6)}
                                    defaultDate={new Date(2022, 3, 12)}
                                    onSelectEvent={event => alert(event.title)}
                                    views={allViews}
                                    events={myEventsList}
                                    eventOverlap
                                    dragRevertDuration={500}
                                    dragScroll
                                    droppable={true}
                                    showMultiDayTimes
                                    step={60}
                                    startAccessor="start"
                                    endAccessor="end"
                                />
                            </CardBody>
                        </Card>
                    </Col>
                </Row>
            </Container>
        </Fragment>
    );
};
export default CalenderContain;