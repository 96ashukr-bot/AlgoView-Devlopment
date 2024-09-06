import React, { Fragment } from 'react';
import { Col, Card, Table, CardHeader } from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import { BreckpointSpecific, Id, Name, OrderId, Price, Quantity, Total } from '../../../../Constant';
import { breckpointSpecific } from '../../../../Data/Table/bootstraptabledata';

const BreckpointClass = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <H3>{BreckpointSpecific}</H3>
                        <span>{'Use'} <code>{'.table-responsive{-sm|-md|-lg|-xl}'}</code> {"functions like a heading for a table. It helps users with screen readers to find a table and understand what it’s about and decide if they want to read it."}</span>
                    </CardHeader>
                    <div className="card-block row">
                        <Col sm="12" lg="12" xl="12">
                            <div className="table-responsive">
                                <Table className="table-responsive-sm">
                                    <thead>
                                        <tr>
                                            <th>{Id}</th>
                                            <th>{Name}</th>
                                            <th>{OrderId}</th>
                                            <th>{Price}</th>
                                            <th>{Quantity}</th>
                                            <th>{Total}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {
                                            breckpointSpecific.map((item) =>
                                                <tr key={item.id}>
                                                    <th scope="row">{item.id}</th>
                                                    <td>{item.name}</td>
                                                    <td>{item.oderid}</td>
                                                    <td>{item.price}</td>
                                                    <td>{item.qty}</td>
                                                    <td>{item.total}</td>
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

export default BreckpointClass;