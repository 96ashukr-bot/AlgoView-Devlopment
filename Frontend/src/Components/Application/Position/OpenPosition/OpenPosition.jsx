import React, { Fragment, useState } from 'react';
import { Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink } from 'reactstrap';
import { H3 } from '../../../../AbstractElements';

const OpenPosition = () => {
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage] = useState(10);

    const tradehistory = []; 

    const indexOfLastSignal = currentPage * itemsPerPage;
    const indexOfFirstSignal = indexOfLastSignal - itemsPerPage;
    const currentSignals = tradehistory.slice(indexOfFirstSignal, indexOfLastSignal);
    const totalPages = Math.ceil(tradehistory.length / itemsPerPage);

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <div className="d-flex justify-content-between align-items-center">
                            <div>
                                <H3>Open Position</H3>
                                {/* <span>{"Below is the list of open positions along with their details."}</span> */}
                            </div>
                        </div>
                    </CardHeader>

                    <div className="card-block row">
                        <Col sm="12" lg="12" xl="12">
                            <div className="table-responsive-sm">
                                <Table>
                                    <thead>
                                        <tr>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>Trade Type</th>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>Signals Type</th>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>Type</th>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>Symbol</th>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>Strategies</th>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>Entry Qty</th>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>Exit Qty</th>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>Live Price</th>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>Entry Price</th>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>Exit Price</th>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>Exit Time</th>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>Stop Loss Time</th>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>Target</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {currentSignals.length === 0 ? (
                                            <tr>
                                                <td colSpan="13" className="text-center">
                                                    No Records Found Right Now
                                                </td>
                                            </tr>
                                        ) : (
                                            currentSignals.map((signal, index) => (
                                                <tr key={index}>
                                                    <td>{signal.entry_type}</td>
                                                    <td>{/* Signal type placeholder */}</td>
                                                    <td>{/* Type placeholder */}</td>
                                                    <td>{signal.symbol}</td>
                                                    <td>{signal.strategy}</td>
                                                    <td>{signal.entry_qty}</td>
                                                    <td>{signal.exit_qty}</td>
                                                    <td>{signal.live_price}</td>
                                                    <td>{signal.entry_price}</td>
                                                    <td>{signal.exit_price}</td>
                                                    <td>{signal.exit_time}</td>
                                                    <td>{/* Stop Loss Time placeholder */}</td>
                                                    <td>{/* Target placeholder */}</td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </Table>
                            </div>

                            <div className="d-flex justify-content-end">
                                <Pagination>
                                    <PaginationItem disabled={currentPage === 1}>
                                        <PaginationLink onClick={() => setCurrentPage(currentPage - 1)}>
                                            Previous
                                        </PaginationLink>
                                    </PaginationItem>
                                    {[...Array(totalPages)].map((_, index) => (
                                        <PaginationItem key={index} active={index + 1 === currentPage}>
                                            <PaginationLink onClick={() => setCurrentPage(index + 1)}>
                                                {index + 1}
                                            </PaginationLink>
                                        </PaginationItem>
                                    ))}
                                    <PaginationItem disabled={currentPage === totalPages}>
                                        <PaginationLink onClick={() => setCurrentPage(currentPage + 1)}>
                                            Next
                                        </PaginationLink>
                                    </PaginationItem>
                                </Pagination>
                            </div>
                        </Col>
                    </div>
                </Card>
            </Col>
        </Fragment>
    );
};

export default OpenPosition;
