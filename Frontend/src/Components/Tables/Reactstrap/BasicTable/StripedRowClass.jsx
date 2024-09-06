import React, { Fragment } from 'react';
import { Col, Card, CardHeader, Table } from 'reactstrap';
import { FirstName, Game, Id, LastName, Point, StripedRow, tablestriped, tablestripedspan, tablestripedspan1, Use } from '../../../../Constant';
import { H3 } from '../../../../AbstractElements';
import { stripedrowtabledata } from '../../../../Data/Table/bootstraptabledata';

const StripedRowClass = () => {

    return (
        <Fragment>
            <Col sm="12" md='6' lg="6" xl="6">
                <Card>
                    <CardHeader>
                        <H3>{StripedRow} </H3>
                        <span>{Use} <code>{tablestriped}</code> {tablestripedspan} <code></code>. {tablestripedspan1}</span>
                    </CardHeader>
                    <div className="card-block row">
                        <Col sm="12">
                            <div className="table-responsive">
                                <Table striped>
                                    <thead>
                                        <tr>
                                            <th scope="col">{Id}</th>
                                            <th scope="col">{FirstName}</th>
                                            <th scope="col">{LastName}</th>
                                            <th scope="col">{Game}</th>
                                            <th scope="col">{Point}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {
                                            stripedrowtabledata.map((item) =>
                                                <tr key={item.id}>
                                                    <th scope="row">{item.id}</th>
                                                    <td>{item.firstname}</td>
                                                    <td>{item.lastname}</td>
                                                    <td>{item.game}</td>
                                                    <td>{item.points}</td>
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
export default StripedRowClass;