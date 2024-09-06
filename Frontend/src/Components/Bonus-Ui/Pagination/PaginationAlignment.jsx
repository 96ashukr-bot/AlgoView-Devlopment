import React from 'react';
import { Col, Card, CardBody, Pagination, PaginationItem, PaginationLink } from 'reactstrap';
import { PaginationAlignment, Previous, Next } from '../../../Constant';
import HeaderCard from '../../Common/Component/HeaderCard';

const PaginationAlignmentClass = () => {
    return (
        <Col xl="12">
            <Card>
                <HeaderCard title={PaginationAlignment} />
                <CardBody>
                    <nav className="m-b-30" aria-label="Page navigation example">
                        <Pagination className="pagination pagination-primary" aria-label="Page navigation example">
                            <PaginationItem><PaginationLink href="#javascript">{Previous}</PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript">{'1'}</PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript">{'2'}</PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript">{'3'}</PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript">{Next}</PaginationLink></PaginationItem>
                        </Pagination>
                    </nav>
                    <nav className="m-b-30" aria-label="Page navigation example">
                        <Pagination className="pagination justify-content-center pagination-primary" aria-label="Page navigation example">
                            <PaginationItem><PaginationLink href="#javascript">{Previous}</PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript">{'1'}</PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript">{'2'}</PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript">{'3'}</PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript">{Next}</PaginationLink></PaginationItem>
                        </Pagination>
                    </nav>
                    <nav aria-label="Page navigation example">
                        <Pagination className="pagination justify-content-end pagination-primary" aria-label="Page navigation example">
                            <PaginationItem><PaginationLink href="#javascript">{Previous}</PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript">{'1'}</PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript">{'2'}</PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript">{'3'}</PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript">{Next}</PaginationLink></PaginationItem>
                        </Pagination>
                    </nav>
                </CardBody>
            </Card>
        </Col>
    );
};

export default PaginationAlignmentClass;