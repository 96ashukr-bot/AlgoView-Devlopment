import React, { Fragment } from 'react';
import { Col, Card, CardHeader, Table } from 'reactstrap';
import { HoverableRows, Id, Schedule, Security, SignalName, Stage, Status, TeamLead } from '../../../../Constant';
import { H3 } from '../../../../AbstractElements';
// import { Hovertabledata } from '../../../../Data/Table/bootstraptabledata';

const HoverableRowsClass = () => {
  return (
    <Fragment>
      <Col sm='12'>
        <Card>
          <CardHeader>
            <H3>{HoverableRows}</H3>
            <span>
              {'Use a class'} <code> {'table-hover'} </code> {'to enable a hover state on table rows within a'} <code>{'tbody'}</code>.
            </span>
          </CardHeader>
          <div className='table-responsive'>
            <Table hover={true} className='table-border-horizontal'>
              <thead>
                <tr>
                  <th scope='col'>{Id}</th>
                  <th scope='col'>{Status}</th>
                  <th scope='col'>{SignalName}</th>
                  <th scope='col'>{Security}</th>
                  <th scope='col'>{Stage}</th>
                  <th scope='col'>{Schedule}</th>
                  <th scope='col'>{TeamLead}</th>
                </tr>
              </thead>
            </Table>
          </div>
        </Card>
      </Col>
    </Fragment>
  );
};

export default HoverableRowsClass;
