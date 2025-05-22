import React, { Fragment, useState, useEffect } from 'react';
import { Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink, Input, Button } from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import './ServiceManagement.css';
import { FaArrowUp, FaArrowDown, } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import { getClientGroupService } from '../../../../Services/Authentication';
import { useParams } from 'react-router-dom';

const ClientDetails = () => {
    const { serviceId } = useParams();
    console.log('Extracted ID:', serviceId);
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage] = useState(10);
    const [searchQuery, setSearchQuery] = useState('');
    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const [clientData, setClientData] = useState([]);
    const navigate = useNavigate();
    const [pagesPerGroup] = useState(4);
    const [currentGroup, setCurrentGroup] = useState(1);

    useEffect(() => {
        fetchData();
    }, [serviceId]);


    const fetchData = async () => {
        try {
            console.log("Extracted ID:", serviceId);

            if (serviceId) {
                const data = await getClientGroupService(serviceId);
                setClientData(data.clients);
            } else {
                console.error("serviceId is missing");
            }
        } catch (error) {
            console.error('Error fetching client data:', error);
        }
    };

    const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });

        const formattedServices = [...clientData].sort((a, b) => {
            if (a[key] < b[key]) return direction === 'asc' ? -1 : 1;
            if (a[key] > b[key]) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        setClientData(formattedServices);
    };

    const filteredServices = clientData.filter(
        (service) =>
            service.client_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            service.service_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            service.license.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const indexOfLastService = currentPage * itemsPerPage;
    const indexOfFirstService = indexOfLastService - itemsPerPage;
    const currentServices = filteredServices.slice(indexOfFirstService, indexOfLastService);
    const totalPages = Math.ceil(filteredServices.length / itemsPerPage);

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
                                <H3>Client Details</H3>
                                {/* <span>{"Below is the list of clients and their associated services."}</span> */}
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
                                            <th onClick={() => handleSort('client_name')} className='custom-col-design'>Client Name <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" />
                                            </th>
                                            <th onClick={() => handleSort('service_name')} className='custom-col-design'>Service Name <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" />
                                            </th>
                                            <th onClick={() => handleSort('license')} className='custom-col-design'>License Type <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" />
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {currentServices.length === 0 ? (
                                            <tr>
                                                <td colSpan="4" style={{ textAlign: 'center' }}>No Client Detail Found</td>
                                            </tr>
                                        ) : (
                                            currentServices.map((service, index) => (
                                                <tr key={service.id}>
                                                    <td>{indexOfFirstService + index + 1}</td>
                                                    <td>{service.client_name}</td>
                                                    <td>{service.service_name}</td>
                                                    <td>{service.license}</td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </Table>
                            </div>

                            {/* Back Button Positioned to the Left Below the Table */}
                            <Col md="12 mb-3">
                                <Button
                                    style={{ marginLeft: '25px' }}
                                    className="mt-3 search-btn-clr"
                                    color="primary"
                                    onClick={() => navigate('/service-manage/group-services-list')}
                                >
                                    Back
                                </Button>
                            </Col>

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

export default ClientDetails;
