import React, { Fragment, useEffect, useState } from 'react';
import { Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink, Input, Button } from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import { FaEye } from 'react-icons/fa';
import { RotatingLines } from 'react-loader-spinner';
import { baseUrl } from '../../../../ConfigUrl/config';
import { useNavigate } from 'react-router';

const LicensePaymentList = () => {
    const [signals, setSignals] = useState([]);
    const [loading, setLoading] = useState(true);
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage] = useState(10);
    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const [searchQuery, setSearchQuery] = useState('');
    const [pagesPerGroup] = useState(4);
    const [currentGroup, setCurrentGroup] = useState(1);
    const navigate = useNavigate();

    useEffect(() => {
        fetchSignals();
    }, []);

    const fetchSignals = async () => {
        try {
            const response = await fetch(`${baseUrl}/order-logs-list`);
            const result = await response.json();
            if (result.status === 'success') {
                setSignals(result.data);
            } else {
                console.error('Error fetching signals:', result.message);
            }
        } catch (error) {
            console.error('Error fetching signals:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleViewClient = () => {
        console.log('View payment:', );
        navigate(`/license/view-license-payment`);
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
                                <H3>License Payment Details</H3>
                            </div>
                            <div className='custom-responsive-style-search'>
                                <Button onClick={() => navigate('/license/license-payment')} className='search-btn-clr'>Buy License</Button>
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
                                            <th onClick={() => handleSort('license_qty')} className='custom-col-design'>License QTY </th>
                                            <th onClick={() => handleSort('license_price')} className='custom-col-design'>License Price </th>
                                            <th onClick={() => handleSort('total')} className='custom-col-design'>Total </th>
                                            <th onClick={() => handleSort('status')} className='custom-col-design'>Status </th>
                                            <th onClick={() => handleSort('view')} className='custom-col-design'>View</th>
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
                                                    {/* <td>{indexOfFirstSignal + index + 1}</td>
                                                    <td>{signal.order_type}</td>
                                                    <td>{signal.symbol}</td>
                                                    <td>{signal.price}</td>
                                                    <td>{signal.strategy}</td>
                                                    <td>
                                                        <FaEye
                                                            onClick={() => handleViewClient()}
                                                            style={{ cursor: 'pointer', marginLeft: '10px' }}
                                                        />
                                                    </td> */}
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
                            <div className="d-flex justify-content-end custom-pagi-style">
                                <Pagination>
                                    <PaginationItem disabled={currentPage === 1}>
                                        <PaginationLink onClick={() => setCurrentPage(currentPage - 1)}>
                                            Previous
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

export default LicensePaymentList;
