import React, { Fragment } from 'react';
import { Breadcrumbs } from '../../../AbstractElements';
import { Container, Row, Col, Card, CardHeader, CardBody } from 'reactstrap';
import { WhetherIconsWithAnimations } from '../../../Constant';
import { weatherIconData } from '../../Common/Data/Icons';

const WeatherIcons = () => {

    return (
        <Fragment>
            <Breadcrumbs parent="Icons" title="Whether Icon" mainTitle="Whether Icon" />
            <Container fluid={true}>
                <Row className="whether-icon">
                    <Col sm="12">
                        <Card>
                            <CardHeader>
                                <h5 className="m-b-0">{WhetherIconsWithAnimations}</h5>
                            </CardHeader>
                            <CardBody>
                                <Row className="icon-lists whether-icon">
                                    {weatherIconData.map((icon, i) =>
                                        <Col lg="2 col-3" key={i}>
                                            {icon.icon}
                                        </Col>
                                    )}
                                </Row>
                            </CardBody>
                        </Card>
                    </Col>
                </Row>
            </Container>
        </Fragment>
    );
};


export default WeatherIcons;