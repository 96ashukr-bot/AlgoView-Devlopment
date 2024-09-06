import React, { Fragment } from 'react';
import { Col, Card, CardHeader, Table } from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import {  ContextualClasses } from '../../../../Constant';

const ContextualClass = () => {
  return (
    <Fragment>
      <Col sm='12'>
        <Card>
          <CardHeader>
            <H3>{ContextualClasses}</H3>
            <span>
              {'Use contextual classes to color table rows or individual cells. you may use Classes'} <code>{'.table-*'}</code>
              {'in'}
              <code>{'tr'}</code>
            </span>
          </CardHeader>
          <Table>
            <thead>
              <tr>
                <th scope='col'>{'Class'}</th>
                <th scope='col'>{'Heading'}</th>
                <th scope='col'>{'Heading'}</th>
              </tr>
            </thead>
            <tbody>
              <tr className='table-primary'>
                <th scope='row'>{'Primary'}</th>
                <td>{'Cell'}</td>
                <td>{'Cell'}</td>
              </tr>
              <tr className='table-secondary'>
                <th scope='row'>{'Secondary'}</th>
                <td>{'Cell'}</td>
                <td>{'Cell'}</td>
              </tr>
              <tr className='table-success'>
                <th scope='row'>{'Success'}</th>
                <td>{'Cell'}</td>
                <td>{'Cell'}</td>
              </tr>
              <tr className='table-info'>
                <th scope='row'>{'Info'}</th>
                <td>{'Cell'}</td>
                <td>{'Cell'}</td>
              </tr>
              <tr className='table-warning'>
                <th scope='row'>{'Warning'}</th>
                <td>{'Cell'}</td>
                <td>{'Cell'}</td>
              </tr>
              <tr className='table-danger'>
                <th scope='row'>{'Danger'}</th>
                <td>{'Cell'}</td>
                <td>{'Cell'}</td>
              </tr>
              <tr className='table-light'>
                <th scope='row'>{'Light'}</th>
                <td>{'Cell'}</td>
                <td>{'Cell'}</td>
              </tr>
              <tr className='table-active'>
                <th scope='row'>{'Active'}</th>
                <td>{'Cell'}</td>
                <td>{'Cell'}</td>
              </tr>
            </tbody>
          </Table>
        </Card>
      </Col>
    </Fragment>
  );
};

export default ContextualClass;
