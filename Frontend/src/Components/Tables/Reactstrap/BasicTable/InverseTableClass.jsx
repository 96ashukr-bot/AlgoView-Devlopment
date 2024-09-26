import React, { Fragment } from 'react';
import { Age, FirstName, insidetable, InverseTable, JoinDate, LastName, Office, Position, Salary, tableinverse, Useclass } from '../../../../Constant';
import { Col, Card, CardHeader, Table } from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
// import { inverse } from '../../../../Data/Table/bootstraptabledata';

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
          </div>
        </Card>
      </Col>
    </Fragment>
  );
};

export default InverseTableClass;
