import React, { Fragment } from 'react';
import { Col, Card, CardHeader, Table } from 'reactstrap';
import { Age, Caption, ContactNo, Email, EmployeeName, Experience, Id, Sex } from '../../../../Constant';
import { H3 } from '../../../../AbstractElements';
import { Captiontabledata } from '../../../../Data/Table/bootstraptabledata';

const CaptionClass = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <H3>{Caption}</H3>
                        <span>{'A'} <code>&lt;{'caption'}&gt;</code> {'functions like a heading for a table. It helps users with screen readers to find a table and understand what it’s about and decide if they want to read it.'}</span>
                    </CardHeader>
                    <div className="card-block row">
                        <Col sm="12" lg="12" xl="12">
                            <div className="table-responsive">
                                <Table>
                                    <caption>{'List of users'}</caption>
                                    <thead>
                                        <tr>
                                            <th scope="col">{Id}</th>
                                            <th scope="col">{EmployeeName}</th>
                                            <th scope="col">{Email}</th>
                                            <th scope="col">{Experience}</th>
                                            <th scope="col">{Sex}</th>
                                            <th scope="col">{ContactNo}</th>
                                            <th scope="col">{Age}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {
                                            Captiontabledata.map((item) =>
                                                <tr key={item.id}>
                                                    <th>{item.id}</th>
                                                    <td>{item.name}</td>
                                                    <td>{item.email}</td>
                                                    <td>{item.exp}</td>
                                                    <td>{item.sex}</td>
                                                    <td>{item.contact}</td>
                                                    <td>{item.age}</td>
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

export default CaptionClass;