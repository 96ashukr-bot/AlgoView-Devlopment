import React from "react";
import { Col, Card, CardBody, Pagination, PaginationItem, PaginationLink } from 'reactstrap'
import { PaginationSizing, Previous, Next } from '../../../Constant'
import HeaderCard from "../../Common/Component/HeaderCard";

const PaginationSizingClass = () => {
    return (
        <Col xl="12">
            <Card>
                <HeaderCard title={PaginationSizing} />
                <CardBody>
                    <Pagination className="m-b-30" aria-label="Page navigation example">
                        <ul className="pagination pagination-lg pagination-primary">
                            <PaginationItem><PaginationLink href="#javascript">{Previous}</PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript">{"1"}</PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript">{"2"}</PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript">{"3"}</PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript">{Next}</PaginationLink></PaginationItem>
                        </ul>
                    </Pagination>
                    <Pagination aria-label="Page navigation example">
                        <ul className="pagination pagination-sm pagination-primary">
                            <PaginationItem><PaginationLink href="#javascript">{Previous}</PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript">{"1"}</PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript">{"2"}</PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript">{"3"}</PaginationLink></PaginationItem>
                            <PaginationItem><PaginationLink href="#javascript">{Next}</PaginationLink></PaginationItem>
                        </ul>
                    </Pagination>
                </CardBody>
            </Card>
        </Col>
    )
}

export default PaginationSizingClass;