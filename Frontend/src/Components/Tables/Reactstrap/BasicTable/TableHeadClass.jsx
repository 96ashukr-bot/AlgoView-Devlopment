import React, { Fragment } from 'react';
import { Col, Card, CardHeader, Table } from 'reactstrap';
import { FirstName, Id, LastName, TableHeadOptions, TableHeadspan, thead, theadlight, theadtext, tomake, Username } from '../../../../Constant';
import { H3 } from '../../../../AbstractElements';
import { Captiontabledata } from '../../../../Data/Table/bootstraptabledata';

const TableHeadClass = () => {
    return (
        <Fragment>
            <Col sm="12" md='6' lg="6" xl="6">
                <Card>
                    <CardHeader>
                        <H3>{TableHeadOptions}</H3>
                        <span>{TableHeadspan} <code>{'.bg-*'}</code>{'and'}  <code>{theadlight}</code> {tomake} <code>{thead}</code> {theadtext}</span>
                    </CardHeader>
                    <div className="card-block row">
                        <Col sm="12">
                            <div className="table-responsive">
                                <Table>
                                    <thead className="table-dark">
                                        <tr>
                                            <th scope="col">{Id}</th>
                                            <th scope="col">{FirstName}</th>
                                            <th scope="col">{LastName}</th>
                                            <th scope="col">{Username}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {
                                            Captiontabledata.slice(0, 3).map((item) =>
                                                <tr key={item.id}>
                                                    <th scope="row">{item.id}</th>
                                                    <td>{item.firstName}</td>
                                                    <td>{item.lastName}</td>
                                                    <td>{item.userName}</td>
                                                </tr>
                                            )
                                        }
                                    </tbody>
                                </Table>
                            </div>
                        </Col>
                    </div>
                </Card>
            </Col>
        </Fragment>
    );
};

export default TableHeadClass;