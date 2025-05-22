import React, { Fragment, useState, useEffect } from 'react';
import {
    Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink,
    Input, Button, Badge
} from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import './Clients.css';
import { FaArrowUp, FaArrowDown } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import { getExpiredClients, SearchAllExpiryClients } from '../../../../Services/Authentication';
import { RotatingLines } from 'react-loader-spinner';
import { debounce } from 'lodash';

const ExpiredClient = () => {
    const [currentPage, setCurrentPage] = useState(1);
    const [clients, setClients] = useState([]);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);
    const [totalPages, setTotalPages] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);
    const [searchQuery, setSearchQuery] = useState('');
    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const [isMobile, setIsMobile] = useState(false);
    const [pageBatch, setPageBatch] = useState(0);
    const navigate = useNavigate();

    const pagesPerBatch = isMobile ? 2 : 4;

    useEffect(() => {
        const handleResize = () => {
            setIsMobile(window.innerWidth <= 768);
        };

        handleResize();
        window.addEventListener('resize', handleResize);

        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const debouncedSearch = debounce(() => {
        if (searchQuery) {
            handleSearch();
        } else {
            fetchExpiredClients();
        }
    }, 500);

    useEffect(() => {
        debouncedSearch();
        return () => debouncedSearch.cancel();
    }, [currentPage, itemsPerPage, searchQuery]);

    const fetchExpiredClients = async () => {
        try {
            setLoading(true);
            const response = await getExpiredClients(currentPage, itemsPerPage);
            console.log('API Response:', response);

            if (response.results && response.results.expiry_client_list) {
                setClients(response.results.expiry_client_list);
                setTotalPages(Math.ceil(response.count / itemsPerPage));
            } else {
                setClients([]);
                setTotalPages(1);
            }
        } catch (err) {
            console.error('Error fetching expired clients:', err);
            setError('Failed to load expired clients.');
            setClients([]);
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = async () => {
        try {
            setLoading(true);
            const response = await SearchAllExpiryClients(searchQuery);
            console.log('Search Response:', response);

            if (response?.results?.expiry_client_list) {
                setClients(response.results.expiry_client_list);
                setTotalPages(Math.ceil(response.count / itemsPerPage) || 1);
            } else {
                setClients([]);
                setTotalPages(1);
            }
        } catch (error) {
            console.error('Error during search:', error);
            setError('Search failed.');
            setClients([]);
            setTotalPages(1);
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

        const sortedClients = [...clients].sort((a, b) => {
            let aValue = '';
            let bValue = '';

            if (key === 'Broker.broker_name') {
                aValue = a.Broker?.broker_name || '';
                bValue = b.Broker?.broker_name || '';
            } else {
                aValue = a[key] || '';
                bValue = b[key] || '';
            }

            if (aValue < bValue) return direction === 'asc' ? -1 : 1;
            if (aValue > bValue) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        setClients(sortedClients);
    };

    const handlePreviousBatch = () => {
        if (pageBatch > 0) setPageBatch(pageBatch - 1);
    };

    const handleNextBatch = () => {
        const maxBatch = Math.ceil(totalPages / pagesPerBatch) - 1;
        if (pageBatch < maxBatch) setPageBatch(pageBatch + 1);
    };

    const handlePageChange = (page) => {
        setCurrentPage(page);
    };

    const handlePrevious = () => {
        if (currentPage > 1) setCurrentPage(currentPage - 1);
    };

    const handleNext = () => {
        if (currentPage < totalPages) setCurrentPage(currentPage + 1);
    };

    const startPage = pageBatch * pagesPerBatch + 1;
    const endPage = Math.min(startPage + pagesPerBatch - 1, totalPages);
    const pages = Array.from({ length: endPage - startPage + 1 }, (_, i) => startPage + i);

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <div className="d-flex justify-content-between align-items-center custom-responsive-style">
                            <div>
                                <H3>Expired Clients</H3>
                            </div>
                            <div className="custom-responsive-style-search">
                                <Input
                                    type="text"
                                    placeholder="Search..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    style={{ width: '200px', display: 'inline-block', marginRight: '10px' }}
                                />
                                <Button className="search-btn-clr" onClick={handleSearch} disabled={loading}>
                                    {loading ? 'Searching...' : 'Search'}
                                </Button>
                            </div>
                        </div>
                    </CardHeader>

                    <div className="card-body">
                        {error && (
                            <div className="text-danger text-center" style={{ padding: '10px' }}>
                                {error}
                            </div>
                        )}
                        <div className="table-responsive">
                            <Table>
                                <thead>
                                    <tr>
                                        <th className="custom-col-design">Sr. No.</th>
                                        <th onClick={() => handleSort('firstName')} className="custom-col-design">
                                            Client Name
                                            <FaArrowUp className="sort-arrow-left" />
                                            <FaArrowDown className="sort-arrow-right" />
                                        </th>
                                        <th onClick={() => handleSort('fullName')} className="custom-col-design">
                                            Full Name
                                            <FaArrowUp className="sort-arrow-left" />
                                            <FaArrowDown className="sort-arrow-right" />
                                        </th>
                                        <th onClick={() => handleSort('Broker.broker_name')} className="custom-col-design">
                                            Broker
                                            <FaArrowUp className="sort-arrow-left" />
                                            <FaArrowDown className="sort-arrow-right" />
                                        </th>
                                        <th onClick={() => handleSort('email')} className="custom-col-design">
                                            Email
                                            <FaArrowUp className="sort-arrow-left" />
                                            <FaArrowDown className="sort-arrow-right" />
                                        </th>
                                        <th onClick={() => handleSort('phoneNumber')} className="custom-col-design">
                                            Phone No.
                                            <FaArrowUp className="sort-arrow-left" />
                                            <FaArrowDown className="sort-arrow-right" />
                                        </th>
                                        <th onClick={() => handleSort('start_date_client')} className="custom-col-design">
                                            From Date
                                            <FaArrowUp className="sort-arrow-left" />
                                            <FaArrowDown className="sort-arrow-right" />
                                        </th>
                                        <th onClick={() => handleSort('end_date_client')} className="custom-col-design">
                                            To Date
                                            <FaArrowUp className="sort-arrow-left" />
                                            <FaArrowDown className="sort-arrow-right" />
                                        </th>
                                        <th onClick={() => handleSort('client_expiry_status')} className="custom-col-design">
                                            Status
                                        </th>
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
                                    ) : clients.length > 0 ? (
                                        clients.map((client, index) => (
                                            <tr key={client.id}>
                                                <td>{(currentPage - 1) * itemsPerPage + index + 1}</td>
                                                <td>{client.firstName || 'N/A'}</td>
                                                <td>{client.fullName || 'N/A'}</td>
                                                <td>{client.Broker?.broker_name || 'N/A'}</td>
                                                <td>{client.email || 'N/A'}</td>
                                                <td>{client.phoneNumber || 'N/A'}</td>
                                                <td>{client.start_date_client || 'N/A'}</td>
                                                <td>{client.end_date_client || 'N/A'}</td>
                                                <td>
                                                    <Badge
                                                        pill
                                                        className="status-pill"
                                                        style={{
                                                            padding: '8px',
                                                            border: `1px solid ${client.client_expiry_status ? 'green' : 'red'}`,
                                                            color: client.client_expiry_status ? 'green' : 'red',
                                                            backgroundColor: 'transparent',
                                                        }}
                                                    >
                                                        {client.client_expiry_status ? 'Active' : 'Inactive'}
                                                    </Badge>
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan="9" style={{ textAlign: 'center', padding: '10px' }}>
                                                No Expired Clients
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </Table>
                        </div>

                        <div className={`d-flex justify-content-end align-items-center ${isMobile ? 'gap-0' : 'gap-0'} custom-pagi-style`}>
                            <p className="mb-0 me-2">Rows per page</p>
                            <Input
                                type="select"
                                value={itemsPerPage}
                                onChange={(e) => {
                                    setItemsPerPage(parseInt(e.target.value));
                                    setCurrentPage(1);
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
                                    <PaginationLink previous onClick={handlePrevious}>
                                        {isMobile ? 'Pre' : 'Previous'}
                                    </PaginationLink>
                                </PaginationItem>

                                {pageBatch > 0 && (
                                    <PaginationItem>
                                        <PaginationLink onClick={handlePreviousBatch}>
                                            {'<'}
                                        </PaginationLink>
                                    </PaginationItem>
                                )}

                                {pages.map((page) => (
                                    <PaginationItem active={page === currentPage} key={page}>
                                        <PaginationLink onClick={() => handlePageChange(page)}>
                                            {page}
                                        </PaginationLink>
                                    </PaginationItem>
                                ))}

                                {endPage < totalPages && (
                                    <PaginationItem>
                                        <PaginationLink onClick={handleNextBatch}>
                                            {'>'}
                                        </PaginationLink>
                                    </PaginationItem>
                                )}

                                <PaginationItem disabled={currentPage === totalPages}>
                                    <PaginationLink next onClick={handleNext}>
                                        Next
                                    </PaginationLink>
                                </PaginationItem>
                            </Pagination>
                        </div>
                    </div>
                </Card>
            </Col>
        </Fragment>
    );
};

export default ExpiredClient;
