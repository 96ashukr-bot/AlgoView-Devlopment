import React, { Fragment } from 'react';
import { Col, Card, Table, CardHeader } from 'reactstrap';
import { H3 } from '../../../AbstractElements';

const RolePermission = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <H3>Role & Permission</H3>
                        <span>{"Below is the list of roles & permission along with their details."}</span>
                    </CardHeader>
                    <div className="card-block row">
                        <Col sm="12" lg="12" xl="12">
                            <div className="table-responsive">
                                <Table className="table-responsive-sm">
                                    <thead>

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

export default RolePermission;