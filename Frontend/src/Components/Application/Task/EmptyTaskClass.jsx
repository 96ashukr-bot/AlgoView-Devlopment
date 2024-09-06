import React, { Fragment } from 'react';
import { Printer } from 'react-feather';
import { Card, CardBody, CardHeader, Row } from 'reactstrap';
import { H6 } from '../../../AbstractElements';
import { NoTaskDueToday, Print } from '../../../Constant';

const EmptyTaskClass = ({ title }) => {
    return (
        <Fragment>
            <Card className="mb-0">
                <CardHeader className="d-flex">
                    <H6 attrH6={{ className: 'mb-0' }} >{title}</H6><a href="#javascript">
                        <Printer className="me-2" />{Print}</a>
                </CardHeader>
                <CardBody>
                    <div className="details-bookmark text-center">
                        <Row></Row>
                        <div className="no-favourite"><span>{NoTaskDueToday}</span></div>
                    </div>
                </CardBody>
            </Card>
        </Fragment>
    );
};
export default EmptyTaskClass;