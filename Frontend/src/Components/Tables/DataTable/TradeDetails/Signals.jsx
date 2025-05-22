import React, { Fragment, useEffect, useState } from 'react';
import { Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink, Input, Button } from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import './TradeDetails.css';
import { RotatingLines } from 'react-loader-spinner';
import { baseUrl } from '../../../../ConfigUrl/config';
import { FaArrowUp, FaArrowDown } from 'react-icons/fa';

const Signals = () => {
    const [signals, setSignals] = useState([]);
    const [loading, setLoading] = useState(true);
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);
    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const [searchQuery, setSearchQuery] = useState('');
    const [isMobile, setIsMobile] = useState(false);
    const [currentGroup, setCurrentGroup] = useState(1);

    useEffect(() => {
        fetchSignals();

        const handleResize = () => {
            setIsMobile(window.innerWidth <= 768);
        };

        handleResize();
        window.addEventListener('resize', handleResize);

        return () => window.removeEventListener('resize', handleResize);

    }, []);

    const pagesPerGroup = isMobile ? 2 : 4;

    const fetchSignals = async () => {
        try {
            const response = await fetch(`${baseUrl}/order-logs-list`);
            const result = await response.json();

            if (result.status === 'success') {
                const allSignals = result.data;

                // Get today's date in YYYY-MM-DD format
                const today = new Date().toISOString().split('T')[0];

                // Filter signals with today's date
                const todaysSignals = allSignals.filter(signal =>
                    signal.signal_time.startsWith(today)
                );

                if (todaysSignals.length > 0) {
                    // If today's signals exist, display them
                    setSignals(todaysSignals);
                } else {
                    // If no signals for today, find the latest signal date from past dates
                    const sortedSignals = allSignals.sort((a, b) =>
                        new Date(b.signal_time) - new Date(a.signal_time)
                    );

                    if (sortedSignals.length > 0) {
                        const lastDate = sortedSignals[0].signal_time.split('T')[0];

                        // Filter all signals with this last available date
                        const lastDateSignals = sortedSignals.filter(signal =>
                            signal.signal_time.startsWith(lastDate)
                        );

                        setSignals(lastDateSignals);
                    } else {
                        setSignals([]);
                    }
                }

            } else {
                console.error('Error fetching signals:', result.message);
            }
        } catch (error) {
            console.error('Error fetching signals:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });

        const sortedSignals = [...signals].sort((a, b) => {
            if (a[key] < b[key]) return direction === 'asc' ? -1 : 1;
            if (a[key] > b[key]) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        setSignals(sortedSignals);
    };

    // Filter signals based on the search query
    const filteredSignals = signals.filter(signal => {
        const signalDate = signal.signal_time ? new Date(signal.signal_time).toLocaleDateString('en-GB') : ''; // Format as dd/mm/yyyy
        const searchLower = searchQuery.toLowerCase();

        return (
            (signalDate && signalDate.includes(searchLower)) ||
            (signal.order_type && signal.order_type.toLowerCase().includes(searchLower)) ||
            (signal.symbol && signal.symbol.toLowerCase().includes(searchLower)) ||
            (signal.strategy && signal.strategy.toLowerCase().includes(searchLower)) ||
            (signal.price && signal.price.toString().includes(searchLower))
        );
    });


    // Pagination logic
    const indexOfLastSignal = currentPage * itemsPerPage;
    const indexOfFirstSignal = indexOfLastSignal - itemsPerPage;
    const currentSignals = filteredSignals.slice(indexOfFirstSignal, indexOfLastSignal);
    const totalPages = Math.ceil(filteredSignals.length / itemsPerPage);

    const totalGroups = Math.ceil(totalPages / pagesPerGroup);

    const currentGroupPages = Array.from(
        { length: Math.min(pagesPerGroup, totalPages - (currentGroup - 1) * pagesPerGroup) },
        (_, idx) => (currentGroup - 1) * pagesPerGroup + idx + 1
    );

    const handlePreviousGroup = () => {
        if (currentGroup > 1) {
            setCurrentGroup(currentGroup - 1);
            setCurrentPage((currentGroup - 2) * pagesPerGroup + 1);
        }
    };

    const handleNextGroup = () => {
        if (currentGroup < totalGroups) {
            setCurrentGroup(currentGroup + 1);
            setCurrentPage(currentGroup * pagesPerGroup + 1);
        }
    };

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <div className="d-flex justify-content-between align-items-center custom-responsive-style">
                            <div>
                                <H3>Signals</H3>
                                {/* <span>{"Below is the list of signals along with their details."}</span> */}
                            </div>
                            <div className='custom-responsive-style-search'>
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
                    </CardHeader>
                    <div className="card-block row">
                        <Col sm="12" lg="12" xl="12">
                            <div className="table-responsive-sm">
                                <Table>
                                    <thead>
                                        <tr>
                                            <th className='custom-col-design'>S.No.</th>
                                            <th onClick={() => handleSort('signal_time')} className='custom-col-design'>Signal Time <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" /></th>
                                            <th onClick={() => handleSort('order_type')} className='custom-col-design'>Order Type <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" /></th>
                                            <th onClick={() => handleSort('symbol')} className='custom-col-design'>Symbol <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" /></th>
                                            <th onClick={() => handleSort('price')} className='custom-col-design'>Price <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" /></th>
                                            <th onClick={() => handleSort('strategy')} className='custom-col-design'>Entry Type <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" /></th>
                                            <th onClick={() => handleSort('created_at')} className='custom-col-design'>Created At <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" /></th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {loading ? (
                                            <tr>
                                                <td colSpan="9" style={{ textAlign: 'center', height: '100px' }}>
                                                    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                                                        <RotatingLines
                                                            strokeColor="#283F7B"
                                                            strokeWidth="4"
                                                            animationDuration="0.75"
                                                            width="50"
                                                            visible={true}
                                                        />
                                                    </div>
                                                </td>
                                            </tr>
                                        ) : currentSignals.length > 0 ? (
                                            currentSignals.map((signal, index) => (
                                                <tr key={index}>
                                                    <td>{indexOfFirstSignal + index + 1}</td>
                                                    <td>{new Date(signal.signal_time).toLocaleString()}</td>
                                                    <td>{signal.order_type}</td>
                                                    <td>{signal.symbol}</td>
                                                    <td>{signal.price}</td>
                                                    <td>{signal.strategy}</td>
                                                    <td>{new Date(signal.created_at).toLocaleString()}</td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan="7" style={{ textAlign: 'center', padding: '10px' }}>
                                                    No Signals Found
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </Table>
                            </div>

                            {/* Pagination */}
                            <div className={`d-flex justify-content-end align-items-center ${isMobile ? 'gap-0' : 'gap-0'} custom-pagi-style`}>
                                <p className="mb-0 me-2">Rows per page</p>
                                <Input
                                    type="select"
                                    value={itemsPerPage}
                                    onChange={(e) => {
                                        setItemsPerPage(parseInt(e.target.value));
                                        setCurrentPage(1); // Reset to page 1 when changing items per page
                                    }}
                                    style={{ width: '80px' }}
                                    className="me-3"
                                >
                                    <option value="10">10</option>
                                    <option value="25">25</option>
                                    <option value="50">50</option>
                                </Input>
                                <Pagination>
                                    <PaginationItem disabled={currentPage === 1}>
                                        <PaginationLink onClick={() => setCurrentPage(currentPage - 1)}>
                                            {isMobile ? 'Pre' : 'Previous'}
                                        </PaginationLink>
                                    </PaginationItem>

                                    <PaginationItem disabled={currentGroup === 1}>
                                        <PaginationLink onClick={handlePreviousGroup}>&lt;</PaginationLink>
                                    </PaginationItem>

                                    {currentGroupPages.map((page) => (
                                        <PaginationItem key={page} active={page === currentPage}>
                                            <PaginationLink onClick={() => setCurrentPage(page)}>
                                                {page}
                                            </PaginationLink>
                                        </PaginationItem>
                                    ))}

                                    <PaginationItem disabled={currentGroup === totalGroups}>
                                        <PaginationLink onClick={handleNextGroup}>&gt;</PaginationLink>
                                    </PaginationItem>

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

export default Signals;
