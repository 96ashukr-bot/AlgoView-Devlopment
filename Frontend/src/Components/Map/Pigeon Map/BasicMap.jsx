import React, { Fragment } from 'react';
import { Card, Col, CardBody, CardHeader } from 'reactstrap';
import { Map } from "pigeon-maps"
import { BasicDemo } from '../../../Constant';
import { H5 } from '../../../AbstractElements';

const BasicMapComp = () => {
    return (
        <Fragment>
            <Col xl="6">
                <Card>
                    <CardHeader>
                        <H5>{BasicDemo}</H5>
                    </CardHeader>
                    <CardBody>
                        <div className="map-js-height" id='map1'>
                            <Map height={500} defaultCenter={[45.879, 4.6997]} defaultZoom={11}>
                            </Map>
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default BasicMapComp;