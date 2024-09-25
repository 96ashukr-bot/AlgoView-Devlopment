import React, { Fragment } from 'react';
import { Col, Card, CardHeader, Table } from 'reactstrap';
import { Calories, Dessert, DessertType, Fat, Id, Price, StripedRowInverseTable, tablestriped, tablestripedspan, tablestripedspan1, Use, Weigth } from '../../../../Constant';
import { H3 } from '../../../../AbstractElements';
// import { stripedwithinverse } from '../../../../Data/Table/bootstraptabledata';

const StripeInverseClass = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <H3>{StripedRowInverseTable}</H3>
                        <span>{Use} <code>{tablestriped}</code> {tablestripedspan} <code></code>. {tablestripedspan1}</span>
                    </CardHeader>
                    <div className="card-block row">
                        <Col sm="12" lg="12" xl="12">
                            <div className="table-responsive">
                                <Table striped className="table-inverse" >
                                    <thead>
                                        <tr>
                                            <th scope="col">{Id}</th>
                                            <th scope="col">{Dessert}</th>
                                            <th scope="col">{DessertType}</th>
                                            <th scope="col">{Calories}</th>
                                            <th scope="col">{Weigth}</th>
                                            <th scope="col">{Fat}</th>
                                            <th scope="col">{Price}</th>
                                        </tr>
                                    </thead>
                                </Table>
                            </div>
                        </Col>
                    </div>
                </Card>
            </Col>
        </Fragment>
    );
};

export default StripeInverseClass;