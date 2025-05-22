import React, { Fragment, useEffect, useState } from 'react';
import { Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink, Input } from 'reactstrap';
import { ToastContainer } from 'react-toastify';
import { FaArrowUp, FaArrowDown, } from 'react-icons/fa';
import 'react-toastify/dist/ReactToastify.css';
import { RotatingLines } from 'react-loader-spinner';
import './ActiveInactive.css';
import { getInactiveClient, SearchInactiveUsers } from '../../../../../Services/Authentication';

const InActiveClient = () => {
    const [userData, setUserData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [totalPages, setTotalPages] = useState([]);
    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const [error, setError] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);
    const [searchQuery, setSearchQuery] = useState('');
    const [pageBatch, setPageBatch] = useState(0);
    const [isMobile, setIsMobile] = useState(false);

    useEffect(() => {
        if (searchQuery) {
            handleSearch();
        } else {
            getUserData();
        }

        const handleResize = () => {
            setIsMobile(window.innerWidth <= 768);
        };

        handleResize();
        window.addEventListener('resize', handleResize);

        return () => window.removeEventListener('resize', handleResize);

    }, [currentPage, itemsPerPage, searchQuery]);

    const pagesPerBatch = isMobile ? 2 : 4;

    const getUserData = async () => {
        try {
            setLoading(true);
            const data = await getInactiveClient(currentPage, itemsPerPage);

            if (data.results && data.results.length > 0) {
                setUserData(data.results); // Directly store the paginated data.
                setTotalPages(Math.ceil(data.count / itemsPerPage));
            } else {
                setUserData([]); // Handle empty pages.
            }
        } catch (err) {
            console.error("Error fetching data:", err);
            setError("Failed to load data.");
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = async () => {
        try {
            setLoading(true);
            const data = await SearchInactiveUsers(searchQuery);
            setUserData(data.results);
            setTotalPages(Math.ceil(data.count / itemsPerPage));
        } catch (err) {
            console.error("Error searching data:", err);
            setError("Failed to search data.");
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

        const sortedClients = [...userData].sort((a, b) => {
            if (a[key] < b[key]) return direction === 'asc' ? -1 : 1;
            if (a[key] > b[key]) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        setUserData(sortedClients);
    };

    const filteredUsers = Array.isArray(userData) ? userData.filter(client =>
        (client.firstName && client.firstName.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (client.lastName && client.lastName.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (client.email && client.email.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (client.phoneNumber && client.phoneNumber.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (client.start_date_client && client.start_date_client && client.start_date_client.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (client.end_date_client && client.end_date_client && client.end_date_client.toLowerCase().includes(searchQuery.toLowerCase()))
    ) : [];

    const indexOfLastUser = currentPage * itemsPerPage;
    const indexOfFirstUser = indexOfLastUser - itemsPerPage;

    let currentUsers = filteredUsers;

    if (currentPage === 1 && filteredUsers.length > itemsPerPage) {
        const extraItem = filteredUsers[filteredUsers.length - 1];
        currentUsers = [extraItem, ...currentUsers.slice(0, itemsPerPage - 1)];
    }

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
            <ToastContainer />
            <Col sm="12">
                <Card style={{ marginTop: '80px' }}>
                    <CardHeader>
                        <div className="d-flex justify-content-between align-items-center custom-responsive-style">
                            <div>
                                <h3>Inactive Clients</h3>
                                {/* <span>Below is the list of Inactive Clients along with their details.</span> */}
                            </div>
                            <div className='custom-responsive-style-search'>
                                <Input
                                    type="text"
                                    placeholder="Search..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    style={{ width: '200px', display: 'inline-block', marginRight: '10px' }}
                                />
                                <button className="btn btn-primary search-btn-clr" onClick={handleSearch}>Search</button>
                            </div>
                        </div>
                    </CardHeader>
                    <div className="card-block row" style={{ height: '100%' }}>
                        <Col sm="12" style={{ height: '100%' }}>
                            <div className="table-responsive" style={{ height: '100%' }}>
                                <Table style={{ height: '100%' }}>
                                    <thead>
                                        <tr>
                                            <th className='custom-col-design'>S.NO</th>
                                            <th className='custom-col-design' onClick={() => handleSort('firstName')}>
                                                First Name <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th className='custom-col-design' onClick={() => handleSort('lastName')}>
                                                Last Name <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            {/* <th style={{ backgroundColor: '#283F7B', color: 'white' }} onClick={() => handleSort('fullName')}>
                                                Full Name {renderSortArrow('fullName')}
                                            </th> */}
                                            <th className='custom-col-design' onClick={() => handleSort('email')}>
                                                Email <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th className='custom-col-design' onClick={() => handleSort('phoneNumber')}>
                                                Phone Number <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th onClick={() => handleSort('start_date_client')} className='custom-col-design'>
                                                Start Date <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th onClick={() => handleSort('end_date_client')} className='custom-col-design'>
                                                End Date <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
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
                                        ) : currentUsers.length > 0 ? (
                                            currentUsers.map((client, index) => (
                                                <tr key={client.id}>
                                                    {/* <td>{index + 1 + (currentPage - 1) * itemsPerPage}</td> */}
                                                    <td>{indexOfFirstUser + index + 1}</td>
                                                    <td>{client.firstName}</td>
                                                    <td>{client.lastName}</td>
                                                    <td>{client.email}</td>
                                                    <td>{client.phoneNumber}</td>
                                                    <td>{client.start_date_client}</td>
                                                    <td>{client.end_date_client}</td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan="7" style={{ textAlign: 'center' }}>No Inactive Clients</td>
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

export default InActiveClient;
