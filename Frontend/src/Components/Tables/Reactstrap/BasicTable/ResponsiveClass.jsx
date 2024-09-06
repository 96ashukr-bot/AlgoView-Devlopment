import React, { Fragment } from 'react';
import { Col, Card, CardHeader, Table } from "reactstrap";
import { H3 } from '../../../../AbstractElements';
import { Assign, Date, Email, Id, Phone, Price, Progress, ResponsiveTables, Status, Task } from '../../../../Constant';
import { responsivetabledata } from '../../../../Data/Table/bootstraptabledata';

const ResponsiveClass = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <H3>{ResponsiveTables}</H3>
                        <span>{"A"} <code>{".table-responsive"}</code>, <code>{'.table-light'}</code> {"inside table element."}</span>
                    </CardHeader>
                    <div className="card-block row">
                        <Col sm="12" lg="12" xl="12">
                            <div className="table-responsive">
                                <Table className='table-light'>
                                    <thead>
                                        <tr>
                                            <th scope="col">{Id}</th>
                                            <th scope="col">{Task}</th>
                                            <th scope="col">{Email}</th>
                                            <th scope="col">{Phone}</th>
                                            <th scope="col">{Assign}</th>
                                            <th scope="col">{Date}</th>
                                            <th scope="col">{Price}</th>
                                            <th scope="col">{Status}</th>
                                            <th scope="col">{Progress}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {
                                            responsivetabledata.map((item) => {
                                                return (
                                                    <tr key={item.id}>
                                                        <th scope='row'>{item.id}</th>
                                                        <td>{item.task}</td>
                                                        <td>{item.email}</td>
                                                        <td>{item.phone}</td>
                                                        <td>{item.assign}</td>
                                                        <td>{item.date}</td>
                                                        <td>{item.price}</td>
                                                        <td className={`${item.status === 'Pending' ? 'text-danger' : 'text-success'}`} >{item.status}</td>
                                                        <td>{item.progress}</td>
                                                    </tr>
                                                )
                                            })
                                        }
                                    </tbody>
                                </Table>
                            </div>
                        </Col>
                    </div>
                </Card>
            </Col>
        </Fragment>
    )
}

export default ResponsiveClass;