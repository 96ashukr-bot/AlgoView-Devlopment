import React, { Fragment, useState, useEffect } from 'react';
import {
    Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink,
    Input, Button, Badge
} from 'reactstrap';
import { useParams } from 'react-router-dom';
import { H3 } from '../../../../../AbstractElements';
import './UserList.css';
import { FaArrowUp, FaArrowDown } from 'react-icons/fa';
import { getActiveInactiveClient } from '../../../../../Services/Authentication';

const UsersView = () => {
    const { userId } = useParams();
    const [currentPage, setCurrentPage] = useState(1);
    const [clients, setClients] = useState([]);
    const [itemsPerPage, setItemsPerPage] = useState(10);
    const [searchQuery, setSearchQuery] = useState('');
    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const [pageBatch, setPageBatch] = useState(0);
    const [isMobile, setIsMobile] = useState(false);

    useEffect(() => {
        fetchClients();

        const handleResize = () => {
            setIsMobile(window.innerWidth <= 768);
        };

        handleResize();
        window.addEventListener('resize', handleResize);

        return () => window.removeEventListener('resize', handleResize);

    }, [userId]);

    const pagesPerBatch = isMobile ? 2 : 4;

    const fetchClients = async () => {
        const storedUserId = localStorage.getItem("userId") || userId;
        if (!storedUserId) {
            console.error("User  ID is missing.");
            return;
        }

        try {
            console.log("Fetching clients for userId:", storedUserId);
            const response = await getActiveInactiveClient(storedUserId);

            // Check for active_inactive_clients instead of results
            if (response?.active_inactive_clients) {
                setClients(response.active_inactive_clients);
                console.log("Clients fetched successfully:", response.active_inactive_clients);
            } else {
                console.warn("No results found in response:", response);
                setClients([]);
            }
        } catch (error) {
            console.error("Error fetching clients:", error);
        }
    };

    const handleSort = (key) => {
        const direction = sortConfig.key === key && sortConfig.direction === 'asc' ? 'desc' : 'asc';
        setSortConfig({ key, direction });

        const sortedClients = [...clients].sort((a, b) => {
            if (a[key] < b[key]) return direction === 'asc' ? -1 : 1;
            if (a[key] > b[key]) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        setClients(sortedClients);
    };


    const filteredClients = clients.filter(client =>
        Object.values(client).some(value =>
            value != null && value.toString().toLowerCase().includes(searchQuery.toLowerCase())
        )
    );

    const indexOfLastClient = currentPage * itemsPerPage;
    const indexOfFirstClient = indexOfLastClient - itemsPerPage;
    const currentClients = filteredClients.slice(indexOfFirstClient, indexOfLastClient);
    const totalPages = Math.ceil(filteredClients.length / itemsPerPage);

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
                                <H3>Client View</H3>
                                {/* <span>{"Below is the list of users along with their details."}</span> */}
                            </div>
                            <div className="d-flex custom-responsive-style-search">
                                <Input
                                    type="text"
                                    placeholder="Search..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    style={{ width: '200px', marginRight: '10px' }}
                                />
                                <Button className='btn btn-primary search-btn-clr'>Search</Button>
                            </div>
                        </div>
                    </CardHeader>

                    <div className="card-block row">
                        <Col sm="12" lg="12" xl="12">
                            <div className="table-responsive-sm">
                                <Table>
                                    <thead>
                                        <tr>
                                            <th className='custom-col-design'>Sr. No.</th>
                                            <th className='custom-col-design' onClick={() => handleSort('client_name')}> Client Name <FaArrowUp className="arrow-icon" /><FaArrowDown className="arrow-icon" /></th>
                                            <th className='custom-col-design' onClick={() => handleSort('assigned_client_name')}> Sub Admin <FaArrowUp className="arrow-icon" /><FaArrowDown className="arrow-icon" /></th>
                                            <th className='custom-col-design' onClick={() => handleSort('client_status')}> Status <FaArrowUp className="arrow-icon" /><FaArrowDown className="arrow-icon" /></th>
                                            <th className='custom-col-design' onClick={() => handleSort('client_phone')}> Phone <FaArrowUp className="arrow-icon" /><FaArrowDown className="arrow-icon" /></th>
                                            <th className='custom-col-design' onClick={() => handleSort('start_date_client')}> Start Date <FaArrowUp className="arrow-icon" /><FaArrowDown className="arrow-icon" /></th>
                                            <th className='custom-col-design' onClick={() => handleSort('end_date_client')}> End Date <FaArrowUp className="arrow-icon" /><FaArrowDown className="arrow-icon" /></th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {currentClients.length > 0 ? (
                                            currentClients.map((client, index) => (
                                                <tr key={index}>
                                                    <td>{indexOfFirstClient + index + 1}</td>
                                                    <td>{client.client_name}</td>
                                                    <td>{client.assigned_client_name || 'N/A'}</td>
                                                    {/* <td>{client.client_status ? 'Active' : 'Inactive'}</td> */}
                                                    <td>
                                                        <Badge
                                                            pill
                                                            className="status-pill"
                                                            style={{
                                                                padding: '8px',
                                                                border: `1px solid ${client.client_status ? 'green' : 'red'}`,
                                                                color: client.client_status ? 'green' : 'red',
                                                                backgroundColor: 'transparent',
                                                            }}
                                                        >
                                                            {client.client_status ? 'Active' : 'Inactive'}
                                                        </Badge>
                                                    </td>
                                                    <td>{client.client_phone}</td>
                                                    <td>{client.start_date_client}</td>
                                                    <td>{client.end_date_client}</td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan="7" style={{ textAlign: 'center' }}>
                                                    No Client found
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
                                    {/* Previous button */}
                                    <PaginationItem disabled={currentPage === 1}>
                                        <PaginationLink previous onClick={handlePrevious}>
                                            {isMobile ? 'Pre' : 'Previous'}
                                        </PaginationLink>
                                    </PaginationItem>

                                    {/* '<' arrow */}
                                    {pageBatch > 0 && (
                                        <PaginationItem>
                                            <PaginationLink onClick={handlePreviousBatch}>&lt;</PaginationLink>
                                        </PaginationItem>
                                    )}

                                    {/* Page numbers */}
                                    {pages.map((page) => (
                                        <PaginationItem active={page === currentPage} key={page}>
                                            <PaginationLink onClick={() => handlePageChange(page)}>{page}</PaginationLink>
                                        </PaginationItem>
                                    ))}

                                    {/* '>' arrow */}
                                    {endPage < totalPages && (
                                        <PaginationItem>
                                            <PaginationLink onClick={handleNextBatch}>&gt;</PaginationLink>
                                        </PaginationItem>
                                    )}

                                    {/* Next button */}
                                    <PaginationItem disabled={currentPage === totalPages}>
                                        <PaginationLink next onClick={handleNext}>
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

export default UsersView;
