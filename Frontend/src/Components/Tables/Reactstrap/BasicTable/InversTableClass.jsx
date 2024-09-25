import React, { Fragment } from 'react';
import { Col, Card, CardHeader, Table } from 'reactstrap';
import { Company, Country, CreditVolume, Email, FirstName, Id, InverseTablePrimaryBackground, inverstablecode, inverstabletext, inverstabletext2, LastName, Role, Useclass } from '../../../../Constant';
import { H3 } from '../../../../AbstractElements';
// import { Inversetabaledata } from '../../../../Data/Table/bootstraptabledata';

const InversePrimaryClass = () => {
  return (
    <Fragment>
      <Col sm='12'>
        <Card>
          <CardHeader>
            <H3>{InverseTablePrimaryBackground}</H3>
            <span>
              {Useclass} <code> {inverstablecode} </code> {inverstabletext}
              <span className='d-block'> {inverstabletext2} </span>
            </span>
          </CardHeader>
          <div className='table-responsive'>
            <Table striped className='bg-primary'>
              <thead>
                <tr>
                  <th scope='col'>{Id}</th>
                  <th scope='col'>{FirstName}</th>
                  <th scope='col'>{LastName}</th>
                  <th scope='col'>{Company}</th>
                  <th scope='col'>{CreditVolume}</th>
                  <th scope='col'>{Email}</th>
                  <th scope='col'>{Role}</th>
                  <th scope='col'>{Country}</th>
                </tr>
              </thead>
            </Table>
          </div>
        </Card>
      </Col>
    </Fragment>
  );
};

export default InversePrimaryClass;
