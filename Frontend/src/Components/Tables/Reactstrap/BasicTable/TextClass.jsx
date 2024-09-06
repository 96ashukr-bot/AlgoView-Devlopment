import React, { Fragment } from 'react';
import { Col, Card, CardHeader, Table } from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import { ColorType, Description, Id, TextBackgroundUtilities } from '../../../../Constant';
import { Backgroundcolordata } from '../../../../Data/Table/bootstraptabledata';

const TextClass = () => {
  return (
    <Fragment>
      <Col sm='12'>
        <Card>
          <CardHeader>
            <H3>{TextBackgroundUtilities}</H3>
            <span>
              {'Regular table background variants are not available with the inverse table, however, you may use Classes'} <code>{'.bg-*'}</code> {'in'}
              <code>{'td'}</code>
            </span>
          </CardHeader>
          <div className='table-responsive'>
            <Table className='table-borderedfor table-border-horizontal'>
              <thead>
                <tr>
                  <th scope='col'>{Id}</th>
                  <th scope='col'>{ColorType}</th>
                  <th scope='col'>{Description}</th>
                </tr>
              </thead>
              <tbody>
                {Backgroundcolordata.map((item) => {
                  return (
                    <tr key={item.id}>
                      <td className={item.class}>{item.id}</td>
                      <td className={item.class}>{item.classname}</td>
                      <td className={item.class}>{item.desc}</td>
                    </tr>
                  );
                })}
              </tbody>
            </Table>
          </div>
        </Card>
      </Col>
    </Fragment>
  );
};
export default TextClass;
