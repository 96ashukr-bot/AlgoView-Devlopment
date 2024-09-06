import React, { Fragment } from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { Map, Marker } from "pigeon-maps"
import { MarkerMap } from '../../../Constant';
import { H5 } from '../../../AbstractElements';

const MarkerMapComp = (props) => {
    return (
        <Fragment>
            <Col xl="6" md="12">
                <Card>
                    <CardHeader>
                        <H5>{MarkerMap}</H5>
                    </CardHeader>
                    <CardBody>
                        <div className="map-js-height">
                            <Map height={500} defaultCenter={[50.879, 4.6997]} defaultZoom={11}>
                                <Marker width={50} anchor={[50.879, 4.6997]} />
                            </Map>
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default MarkerMapComp;