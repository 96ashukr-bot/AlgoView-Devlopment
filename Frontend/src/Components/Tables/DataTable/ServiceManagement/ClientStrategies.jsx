import React, { Fragment, useEffect, useState } from 'react';
import { Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink, Input, Button } from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import { useNavigate, useParams } from 'react-router-dom';
import './ServiceManagement.css';
import { RotatingLines } from 'react-loader-spinner';
import { FaArrowUp, FaArrowDown } from 'react-icons/fa';
import { getStrategyClient } from '../../../../Services/Authentication';

const ClientStrategies = () => {
    const { id } = useParams();
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage,setItemsPerPage] = useState(10);
    const [clients, setClients] = useState([]);
    const [loading, setLoading] = useState('');
    const [searchQuery, setSearchQuery] = useState('');
    const [clientData, setClientData] = useState([]);
    const navigate = useNavigate();
    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const [isMobile, setIsMobile] = useState(false);
    const [currentGroup, setCurrentGroup] = useState(1);

    useEffect(() => {
        if (id) {
            getStrategyClient(id)
                .then(data => {
                    console.log("Received Data:", data);
                    setClientData(Array.isArray(data.clients) ? data.clients : []);
                    setLoading(false);
                })
                .catch(err => {
                    console.error("Error fetching client data:", err);
                    setLoading(false);
                });
        }

        const handleResize = () => {
            setIsMobile(window.innerWidth <= 768);
        };

        handleResize();
        window.addEventListener('resize', handleResize);

        return () => window.removeEventListener('resize', handleResize);

    }, [id]);

    const pagesPerGroup = isMobile ? 2 : 4;

    const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });

        const sortedClients = [...clients].sort((a, b) => {
            if (a[key] < b[key]) return direction === 'asc' ? -1 : 1;
            if (a[key] > b[key]) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        setClients(sortedClients);
    };

    const filteredClients = clientData.filter((client) =>
        client.firstName.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const indexOfLastClient = currentPage * itemsPerPage;
    const indexOfFirstClient = indexOfLastClient - itemsPerPage;
    const currentClients = filteredClients.slice(indexOfFirstClient, indexOfLastClient);
    const totalPages = Math.ceil(filteredClients.length / itemsPerPage);

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
                                <H3>Client Strategies</H3>
                                {/* <span>{"Below is the list of clients along with their strategy details."}</span> */}
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
                                            <th className='custom-col-design'>Sr. No.</th>
                                            <th onClick={() => handleSort('firstname')} className='custom-col-design'>Client Name <FaArrowUp className="sort-arrow-left" /> <FaArrowDown className="sort-arrow-right" /></th>
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
                                        ) : currentClients.length > 0 ? (
                                            currentClients.map((client, index) => (
                                                <tr key={client.id}>
                                                    <td>{indexOfFirstClient + index + 1}</td>
                                                    <td>{client.firstName}</td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan="2" style={{ textAlign: 'center' }}>No Client Strategies Found</td>
                                            </tr>
                                        )}
                                    </tbody>
                                </Table>
                            </div>
                            {/* Back Button */}
                            <div className="d-flex justify-content-start" style={{ margin: '10px' }}>
                                <Button
                                    className='search-btn-clr'
                                    onClick={() => navigate('/service-manage/strategies')}
                                >
                                    Back
                                </Button>
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

export default ClientStrategies;
