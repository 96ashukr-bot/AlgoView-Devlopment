import React, { Fragment } from 'react';
import { Container, Row, Col, Card, CardBody } from 'reactstrap';
import { Breadcrumbs } from '../../../AbstractElements';
import HeaderCard from '../../Common/Component/HeaderCard';
import DataTableComponent from './DataTableComponent';

const DataTables = () => {

  return (
    <Fragment>
      <Breadcrumbs parent="Table" title="Data Tables" mainTitle="Data Tables" />
      <Container fluid={true}>
        <Row>
          <Col sm="12">
            <Card>
              <HeaderCard title="Select Multiple and Delete Single Data" />
              <CardBody>
                <DataTableComponent />
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </Fragment>
  );

};

export default DataTables;