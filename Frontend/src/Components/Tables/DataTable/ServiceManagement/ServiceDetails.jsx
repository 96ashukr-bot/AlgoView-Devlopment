import React, { Fragment, useEffect, useState } from 'react';
import { Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink, Input, Button } from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import { useNavigate, useParams } from 'react-router-dom';
import './ServiceManagement.css';
import { FaArrowUp, FaArrowDown, } from 'react-icons/fa';
import { getGroupServiceQtyDetails } from '../../../../Services/Authentication';

const ServiceDetails = () => {
    const navigate = useNavigate();
    const { serviceId } = useParams();
    console.log('Extracted ID:', serviceId);
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage] = useState(10);
    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const [searchQuery, setSearchQuery] = useState('');
    const [services, setServices] = useState([]);
    const [pagesPerGroup] = useState(4);
    const [currentGroup, setCurrentGroup] = useState(1);

    useEffect(() => {
        fetchServiceDetails();
    }, [serviceId]);


    const fetchServiceDetails = async () => {
        try {
            console.log("Extracted ID:", serviceId);
            const response = await getGroupServiceQtyDetails(serviceId);
            const data = response.json_data || [];

            const formattedServices = data.map((item) => ({
                service_name: item["ServiceName"],
                group_qty: item.Qty,
            }));
            setServices(formattedServices);
        } catch (error) {
            console.error('Error fetching service details:', error);
        }
    };

    const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });

        const formattedServices = [...services].sort((a, b) => {
            if (a[key] < b[key]) return direction === 'asc' ? -1 : 1;
            if (a[key] > b[key]) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        setServices(formattedServices);
    };

    const filteredServices = services.filter((service) =>
        (service.service_name?.toLowerCase() || '').includes(searchQuery?.toLowerCase() || '') ||
        service.group_qty?.toString().includes(searchQuery || '')
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
                                <H3>Service Details</H3>
                                {/* <span>{"Below is the list of services along with their details."}</span> */}
                            </div>
                            <div className='custom-responsive-style-search'>
                                <Input
                                    type="text"
                                    placeholder="Search..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    style={{ width: '200px', display: 'inline-block', marginRight: '10px' }}
                                />
                                <Button className="search-btn-clr">Search</Button>
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
                                            <th onClick={() => handleSort('service_name')} className='custom-col-design'>Service Name <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" />
                                            </th>
                                            <th onClick={() => handleSort('group_qty')} className='custom-col-design'>Group Qty <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" />
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {currentServices.length === 0 ? (
                                            <tr>
                                                <td colSpan="3" style={{ textAlign: 'center' }}>No Service Details Found</td>
                                            </tr>
                                        ) : (
                                            currentServices.map((service, index) => (
                                                <tr key={index}>
                                                    <td>{indexOfFirstService + index + 1}</td>
                                                    <td>{service.service_name}</td>
                                                    <td>{service.group_qty}</td>
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
                            <div className="d-flex justify-content-end mt-3 custom-pagi-style">
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

export default ServiceDetails;