import React, { Fragment } from 'react';
import { Age, FirstName, insidetable, InverseTable, JoinDate, LastName, Office, Position, Salary, tableinverse, Useclass } from '../../../../Constant';
import { Col, Card, CardHeader, Table } from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import { inverse } from '../../../../Data/Table/bootstraptabledata';

const InverseTableClass = () => {
  return (
    <Fragment>
      <Col sm='12'>
        <Card>
          <CardHeader>
            <H3>{InverseTable}</H3>
            <span>
              {Useclass} <code>{tableinverse}</code> {insidetable}
            </span>
          </CardHeader>
          <div className='table-responsive'>
            <Table className='table-inverse'>
              <thead>
                <tr>
                  <th scope='col'>{'#'}</th>
                  <th scope='col'>{FirstName}</th>
                  <th scope='col'>{LastName}</th>
                  <th scope='col'>{Office}</th>
                  <th scope='col'>{Position}</th>
                  <th scope='col'>{Salary}</th>
                  <th scope='col'>{JoinDate}</th>
                  <th scope='col'>{Age}</th>
                </tr>
              </thead>
              <tbody>
                {inverse.map((item) => (
                  <tr key={item.id}>
                    <th scope='row'>{item.id}</th>
                    <td>{item.firstName}</td>
                    <td>{item.lastName}</td>
                    <td>{item.office}</td>
                    <td>{item.role}</td>
                    <td>{item.salary}</td>
                    <td>{item.join}</td>
                    <td>{item.age}</td>
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

export default InverseTableClass;
