import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';
import GeoJsonMap from './GeoJsonMap';
import BasicMapComp from './BasicMap';
import MarkerMapComp from './MarkerMap';
import DraggableMarker from './DraggableMarker';
import { Breadcrumbs } from '../../../AbstractElements';

const PigeonMap = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle='Pigeon Maps' parent='Maps' title='Pigeon Maps' />
      <Container fluid={true}>
        <Row>
          <BasicMapComp />
          <MarkerMapComp />
          <DraggableMarker />
          <GeoJsonMap />
        </Row>
      </Container>
    </Fragment>
  );
};

export default PigeonMap;
