import React, { Fragment, useState } from 'react';
import { Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink, Input, Button, Form, FormGroup, Label, Row } from 'reactstrap';
import { FaDollarSign } from 'react-icons/fa'; 
import { H3 } from '../../../../AbstractElements';

const OptionChain = () => {
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage] = useState(10);
    const [searchQuery, setSearchQuery] = useState('');
    const [formData, setFormData] = useState({
        symbol: '',
        expiryDate: '',
        strategy: '',
        price: 1,
    });

    const tradehistory = [
        {
            entry_time: '2024-10-01T10:00:00Z',
            exit_time: '2024-10-01T12:00:00Z',
            symbol: 'AAPL',
            strategy: 'Long',
            entry_type: 'Buy',
            entry_qty: 10,
            exit_qty: 5,
            live_price: 155.0,
            entry_price: 150.0,
            exit_price: 152.0,
            total: 50,
        },
        {
            entry_time: '2024-10-02T10:00:00Z',
            exit_time: '2024-10-02T12:00:00Z',
            symbol: 'GOOGL',
            strategy: 'Short',
            entry_type: 'Sell',
            entry_qty: 15,
            exit_qty: 10,
            live_price: 2800.0,
            entry_price: 2750.0,
            exit_price: 2780.0,
            total: 300,
        },
    ];

    const indexOfLastSignal = currentPage * itemsPerPage;
    const indexOfFirstSignal = indexOfLastSignal - itemsPerPage;
    const currentSignals = tradehistory.slice(indexOfFirstSignal, indexOfLastSignal);
    const totalPages = Math.ceil(tradehistory.length / itemsPerPage);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({ ...formData, [name]: value });
    };

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                    <div className="d-flex justify-content-between align-items-center">
                            <div>
                                <H3>Option Chain</H3>
                                <span>{"Below is the list of Option Chain along with their details."}</span>
                            </div>
                            <div>
                                <Input
                                    type="text"
                                    placeholder="Search..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    style={{ width: '200px', display: 'inline-block', marginRight: '10px' }}
                                />
                                <Button className='search-btn-clr'>Search</Button>
                            </div>
                        </div>
                        <Form className="mt-3">
                            <Row form>
                                <Col md={3}>
                                    <FormGroup>
                                        <Label for="symbol">Symbol</Label>
                                        <Input
                                            type="select"
                                            name="symbol"
                                            id="symbol"
                                            value={formData.symbol}
                                            onChange={handleInputChange}
                                        >
                                            <option value="">All</option>
                                            <option value="AAPL">AAPL</option>
                                            <option value="GOOGL">GOOGL</option>
                                        </Input>
                                    </FormGroup>
                                </Col>
                                <Col md={3}>
                                    <FormGroup>
                                        <Label for="expiryDate">Expiry Date</Label>
                                        <Input
                                            type="date"
                                            name="expiryDate"
                                            id="expiryDate"
                                            value={formData.expiryDate}
                                            onChange={handleInputChange}
                                        />
                                    </FormGroup>
                                </Col>
                                <Col md={3}>
                                    <FormGroup>
                                        <Label for="strategy">Strategy</Label>
                                        <Input
                                            type="select"
                                            name="strategy"
                                            id="strategy"
                                            value={formData.strategy}
                                            onChange={handleInputChange}
                                        >
                                            <option value="">All</option>
                                            <option value="Long">Long</option>
                                            <option value="Short">Short</option>
                                        </Input>
                                    </FormGroup>
                                </Col>
                                <Col md={3}>
                                    <FormGroup>
                                        <Label for="price">Price</Label>
                                        <Input
                                            type="number"
                                            name="price"
                                            id="price"
                                            value={formData.price}
                                            onChange={handleInputChange}
                                            min={1}
                                        />
                                    </FormGroup>
                                </Col>
                            </Row>
                        </Form>
                    </CardHeader>

                    <div className="card-block row">
                        <Col sm="12" lg="12" xl="12">
                            <div className="table-responsive-sm">
                                <Table>
                                    <thead>
                                        <tr>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>BUY/SELL</th>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>CALL/LP</th>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>STRIKE PRICE</th>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>PUT/LP</th>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>BUY/SELL</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {currentSignals.map((signal, index) => (
                                            <tr key={index}>
                                                <td>
                                                    {/* Green Dollar Icon (Left) & Red Dollar Icon (Right) */}
                                                    <FaDollarSign color="green" style={{ marginRight: '10px' }} />
                                                    <FaDollarSign color="red" />
                                                </td>
                                                <td>{signal.live_price}</td>
                                                <td>{signal.entry_price}</td>
                                                <td>{signal.exit_price}</td>
                                                <td>
                                                    {/* Buy/Sell Indicator */}
                                                    {signal.entry_type === 'Buy' ? (
                                                        <FaDollarSign color="green" />
                                                    ) : (
                                                        <FaDollarSign color="red" />
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
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

export default OptionChain;
