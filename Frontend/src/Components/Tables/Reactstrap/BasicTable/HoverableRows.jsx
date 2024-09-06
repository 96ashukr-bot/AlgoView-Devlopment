import React, { Fragment } from 'react';
import { Col, Card, CardHeader, Table } from 'reactstrap';
import { HoverableRows, Id, Schedule, Security, SignalName, Stage, Status, TeamLead } from '../../../../Constant';
import { H3 } from '../../../../AbstractElements';
import { Hovertabledata } from '../../../../Data/Table/bootstraptabledata';

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
              <tbody>
                {Hovertabledata.map((item) => (
                  <tr key={item.id}>
                    <th scope='row'>{item.id}</th>
                    <td className='d-flex align-items-center'>
                      <span className={`${item.bgClass} rounded-1 p-1 me-2 d-flex align-items-center`}>{item.icon}</span>
                      {item.status}
                    </td>
                    <td>{item.signalName}</td>
                    <td>{item.security}</td>
                    <td>{item.stage}</td>
                    <td>{item.schedule}</td>
                    <td>{item.teamLead}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </div>
        </Card>
      </Col>
    </Fragment>
  );
};

export default HoverableRowsClass;
