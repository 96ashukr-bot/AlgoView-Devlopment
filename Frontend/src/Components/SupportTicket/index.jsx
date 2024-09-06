import { Breadcrumbs, H5 } from '../../AbstractElements';
import TicketList from './TicketList';
import TicketTable from './TicketTable';
import { Card, CardBody, CardHeader, Col, Container, Row } from 'reactstrap';
import React, { Fragment } from 'react';

const SupportTickitContain = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle='Support Ticket' parent='Apps' title='Support Ticket' />
      <Container fluid={true}>
        <Row>
          <Col sm='12'>
            <Card>
              <CardHeader>
                <H5>{'Support Ticket List'}</H5>
                <span>{'List of ticket opend by customers'}</span>
              </CardHeader>
              <CardBody>
                <TicketList />
                <TicketTable />
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
};
export default SupportTickitContain;
