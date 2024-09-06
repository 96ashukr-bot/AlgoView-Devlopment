import React, { Fragment } from 'react';
import { Col, Card, CardHeader, Table } from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import { classname, DashedBorder, Hours, Id, Spots, Trainer, Type } from '../../../../Constant';
import { dashedborderdata } from '../../../../Data/Table/bootstraptabledata';

const DashedBorderClass = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <H3>{DashedBorder}</H3>
                        <span>{'Example of a'} <code>{'dashed'}</code> {'border inside table head. This border has'} <code>{'3px'}</code> {'width,'} <code>{'dashed'}</code> {'style and inherits all styling options from the default border style. Visually it displays table'} <code>{'head'}</code> {'and'} <code>{'body'}</code> {'as 2 separated table areas. To use this border add'} <code>{'.border-dashed'}</code> {'to the table head row.'}</span>
                    </CardHeader>
                    <div className="table-responsive">
                        <Table className='table-dashed'>
                            <thead>
                                <tr className="dashed">
                                    <th scope="col">{Id}</th>
                                    <th scope="col">{classname}</th>
                                    <th scope="col">{Type}</th>
                                    <th scope="col">{Hours}</th>
                                    <th scope="col">{Trainer}</th>
                                    <th scope="col">{Spots}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {
                                    dashedborderdata.map((item) =>
                                        <tr className="dashed" key={item.id}>
                                            <th scope="row">{item.id}</th>
                                            <td>{item.name}</td>
                                            <td>{item.type}</td>
                                            <td>{item.time}</td>
                                            <td>{item.trainer}</td>
                                            <td>{item.spots}</td>
                                        </tr>
                                    )
                                }
                            </tbody>
                        </Table>
                    </div>
                </Card>
            </Col>
        </Fragment>
    );
};

export default DashedBorderClass;