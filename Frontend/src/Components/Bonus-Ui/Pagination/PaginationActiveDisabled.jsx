import React from 'react';
import { Col, Card, CardBody, Pagination, PaginationItem, PaginationLink } from 'reactstrap';
import { PaginationActiveDisabled, Previous, Next } from '../../../Constant';
import HeaderCard from '../../Common/Component/HeaderCard';

const PaginationActiveDisabledClass = () => {
    return (
        <Col xl="12">
            <Card>
                <HeaderCard title={PaginationActiveDisabled} />
                <CardBody>
                    <Pagination aria-label="...">
                        <ul className="pagination pagination-primary">
                            <PaginationItem disabled><PaginationLink>{Previous}</PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript" >{'1'}</PaginationLink></PaginationItem>
                            <PaginationItem active><PaginationLink href="#javascript">{'2'} <span className="sr-only">{'(current)'}</span></PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript">{'3'}</PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript">{Next}</PaginationLink></PaginationItem>
                        </ul>
                    </Pagination>
                </CardBody>
            </Card>
        </Col>
    );
};

export default PaginationActiveDisabledClass;