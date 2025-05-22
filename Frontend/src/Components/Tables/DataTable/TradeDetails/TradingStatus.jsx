import React, { Fragment, useState, useEffect } from 'react';
import { Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink, Input, Button } from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import { FaArrowUp, FaArrowDown, } from 'react-icons/fa';
import { RotatingLines } from 'react-loader-spinner';
import Swal from 'sweetalert2';
import { getClientTradeStatus, updateClientTradeStatus, TradeStatusSearch } from '../../../../Services/Authentication';
import './TradeDetails.css'

const TradingStatus = () => {
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);
    const [error, setError] = useState(null);
    const [totalPages, setTotalPages] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [tradingStatus, setTradingStatus] = useState([]);
    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const [loading, setLoading] = useState(false);
    const [isMobile, setIsMobile] = useState(false);
    const [pageBatch, setPageBatch] = useState(0);

    useEffect(() => {
        if (searchQuery) {
            handleSearch();
        } else {
            fetchTradingStatus();
        }

        const handleResize = () => {
            setIsMobile(window.innerWidth <= 768);
        };

        handleResize();
        window.addEventListener('resize', handleResize);

        return () => window.removeEventListener('resize', handleResize);

    }, [currentPage, itemsPerPage, searchQuery]);

    const pagesPerBatch = isMobile ? 2 : 4;

    const fetchTradingStatus = async () => {
        try {
            setLoading(true);
            const response = await getClientTradeStatus(currentPage, itemsPerPage);

            if (response.results && response.results.length > 0) {
                setTradingStatus(response.results);
                setTotalPages(Math.ceil(response.count / itemsPerPage));
            } else {
                setTradingStatus([]);
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
            const response = await TradeStatusSearch(searchQuery);
            if (response?.results?.length > 0) {
                setTradingStatus(response.results);
            } else {
                setTradingStatus([]);
            }
        } catch (error) {
            console.error('Error during search:', error);
            setError("Search failed.");
        } finally {
            setLoading(false);
        }
    };

    const toggleTradingStatus = async (clientId, currentState) => {
        const payload = { is_enable: !currentState };
        try {
            const response = await updateClientTradeStatus(clientId, payload);
            const updatedEnableState = response.data.is_enable;

            Swal.fire(
                "Success!",
                `Client status updated to ${updatedEnableState ? '"Active"' : '"Inactive"'}.`,
                "success"
            );

            // Update the state
            const updatedTradingStatus = tradingStatus.map((client) =>
                client.id === clientId
                    ? { ...client, is_enable: updatedEnableState }
                    : client
            );
            setTradingStatus(updatedTradingStatus);
        } catch (error) {
            console.error("Error updating client status:", error);
            Swal.fire("Error!", "Could not update client status. Please try again.", "error");
        }
    };

    const filteredTradingStatus = tradingStatus.filter(status =>
        (status.fullName && status.fullName.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (status.email && status.email.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (status.phoneNumber && status.phoneNumber.includes(searchQuery)) ||
        (status.end_date_client && status.end_date_client.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });

        const sortedStatus = [...tradingStatus].sort((a, b) => {
            if (a[key] < b[key]) return direction === 'asc' ? -1 : 1;
            if (a[key] > b[key]) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        setTradingStatus(sortedStatus);
    };

    const indexOfLastStatus = currentPage * itemsPerPage;
    const indexOfFirstStatus = indexOfLastStatus - itemsPerPage;

    let currentTradingStatus = filteredTradingStatus;

    if (currentPage === 1 && filteredTradingStatus.length > itemsPerPage) {
        const extraItem = filteredTradingStatus[filteredTradingStatus.length - 1];
        currentTradingStatus = [extraItem, ...currentTradingStatus.slice(0, itemsPerPage - 1)];
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
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <div className="d-flex justify-content-between align-items-center custom-responsive-style">
                            <div>
                                <H3>Trading Status</H3>
                                {/* <span>{"Below is the list of clients along with their trading status."}</span> */}
                            </div>
                            {/* <hr /> */}
                            <div className='custom-responsive-style-search'>
                                <Input
                                    type="text"
                                    placeholder="Search..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter') {
                                            handleSearch();
                                        }
                                    }}
                                    style={{ width: '200px', display: 'inline-block', marginRight: '10px' }}
                                />
                                <Button className='search-btn-clr' onClick={handleSearch}>Search</Button>
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
                                            <th className='custom-col-design' onClick={() => handleSort('fullName')}>
                                                Full Name <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th className='custom-col-design' onClick={() => handleSort('email')}>
                                                Email <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th className='custom-col-design' onClick={() => handleSort('phoneNumber')}>
                                                Phone Number <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th className='custom-col-design'>Trading ON/OFF</th>
                                            {/* <th style={{ backgroundColor: '#283F7B', color: 'white' }}>Start Date</th> */}
                                            <th className='custom-col-design' onClick={() => handleSort('end_date_client')}>End Date <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" /></th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {loading ? (
                                            <tr>
                                                <td colSpan="6" style={{ textAlign: 'center', height: '100px' }}>
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
                                        ) : currentTradingStatus.length === 0 ? (
                                            <tr>
                                                <td colSpan="6" style={{ textAlign: 'center' }}>
                                                    No Trading Status Found
                                                </td>
                                            </tr>
                                        ) : (
                                            currentTradingStatus.map((status, index) => (
                                                <tr key={index}>
                                                    <td>{indexOfFirstStatus + index + 1}</td>
                                                    <td>{status.fullName}</td>
                                                    <td>{status.email}</td>
                                                    <td>{status.phoneNumber}</td>
                                                    <td>
                                                        <label className="switch">
                                                            <input
                                                                type="checkbox"
                                                                checked={status.is_enable}
                                                                onChange={() => toggleTradingStatus(status.id, status.is_enable)}
                                                            />
                                                            <span className="slider round"></span>
                                                        </label>
                                                    </td>
                                                    <td>{status.end_date_client}</td>
                                                </tr>
                                            ))
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

export default TradingStatus;
