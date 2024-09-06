import React, { Fragment } from 'react';
import { Col, Card, CardHeader, Table } from 'reactstrap';
import { Date, EmployeeName, Hours, Id, Performance, sizetable, Status } from '../../../../Constant';
import { H3 } from '../../../../AbstractElements';
import { Sizingtabledata } from '../../../../Data/Table/bootstraptabledata';

const Sizingtable = () => {

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <H3>{sizetable}</H3>
                        <span>{'Example of Extra large table, Add'} <code>{'.table-xl'}</code>, <code>{'.table-lg'}</code>, <code>{'.table-sm'}</code>, <code>{'.table-xs'}</code> {'class in table tag for change table size'}</span>
                    </CardHeader>
                    <div className="card-block row">
                        <Col sm="12" lg="12" xl="12">
                            <div className="table-responsive">
                                <Table size='lg'>
                                    <thead className="thead-dark">
                                        <tr>
                                            <th scope="col">{Id}</th>
                                            <th scope="col">{EmployeeName}</th>
                                            <th scope="col">{Date}</th>
                                            <th scope="col">{Status}</th>
                                            <th scope="col">{Hours}</th>
                                            <th scope="col">{Performance}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {
                                            Sizingtabledata.map((item) =>
                                                <tr key={item.id}>
                                                    <th scope="row">{item.id}</th>
                                                    <td>{item.name}</td>
                                                    <td>{item.date}</td>
                                                    <td className={`${item.status === 'On leave' ? 'text-danger' : 'text-success'}`} >{item.status}</td>
                                                    <td>{item.time}</td>
                                                    <td>{item.performance}</td>
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

export default Sizingtable;