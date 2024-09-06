import React, { Fragment } from 'react';
import { Row, Col, Card, CardHeader, Table } from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import { Budget, CustomTableColorHoverStripped, DomesticGross, FilmTitle, Id, Released, Studio } from '../../../../Constant';
import { customtablecolor } from '../../../../Data/Table/bootstraptabledata';

const CustomHoverClass = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <H3>{CustomTableColorHoverStripped}</H3>
                        <span>{'Use class'}<code>{'table-hover, table-striped table-*'}</code><code>{'table-info'}</code>,<code>{'table-success'}</code>,<code>{'table-success'}</code>,<code>{'table-info'}</code>,<code>{'table-danger'}</code>,<code>{'table-primary'}</code>,<code>{'table-secondary'}</code>,<code>{'table-light'}</code>,<code>{'table-active'}</code> {'inside table element.'}</span>
                    </CardHeader>
                    <Row className="card-block">
                        <Col sm="12" lg="12" xl="12">
                            <div className="table-responsive table-border-radius">
                                <Table hover striped className="table-styling  table-primary">
                                    <thead>
                                        <tr>
                                            <th scope="col">{Id}</th>
                                            <th scope="col">{FilmTitle}</th>
                                            <th scope="col">{Released}</th>
                                            <th scope="col">{Studio}</th>
                                            <th scope="col">{Budget}</th>
                                            <th scope="col">{DomesticGross}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {
                                            customtablecolor.map((item) =>
                                                <tr key={item.id}>
                                                    <th scope="row">{item.id}</th>
                                                    <td>{item.title}</td>
                                                    <td>{item.releaseddate}</td>
                                                    <td>{item.studio}</td>
                                                    <td>{item.budget}</td>
                                                    <td>{item.gross}</td>
                                                </tr>
                                            )
                                        }
                                    </tbody>
                                </Table>
                            </div>
                        </Col>
                    </Row>
                </Card>
            </Col>
        </Fragment>
    );
};
export default CustomHoverClass;