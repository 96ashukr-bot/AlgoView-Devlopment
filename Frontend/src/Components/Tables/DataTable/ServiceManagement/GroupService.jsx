import React, { Fragment, useEffect, useState } from 'react';
import { Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink, Input, Button } from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import { FaTools, FaArrowUp, FaArrowDown, FaPencilAlt, FaTrashAlt } from 'react-icons/fa';
import { useNavigate } from 'react-router';
import { RotatingLines } from 'react-loader-spinner';
import './ServiceManagement.css'
import Swal from 'sweetalert2';
import { getGroupServices, deleteGroupServices } from '../../../../Services/Authentication';

const GroupService = () => {
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);
    const [totalPages, setTotalPages] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const [services, setServices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [groupServices, setGroupServices] = useState([]);
    const navigate = useNavigate();
    const [isMobile, setIsMobile] = useState(false);
    const [pageBatch, setPageBatch] = useState(0);

    useEffect(() => {
        fetchGroupServices(searchQuery);

        const handleResize = () => {
            setIsMobile(window.innerWidth <= 768);
        };

        handleResize();
        window.addEventListener('resize', handleResize);

        return () => window.removeEventListener('resize', handleResize);

    }, [currentPage, itemsPerPage, searchQuery]);

    const pagesPerBatch = isMobile ? 2 : 4;

    const fetchGroupServices = async (query = '') => {
        try {
            setLoading(true);
            const response = await getGroupServices(currentPage, itemsPerPage, query);

            if (response.results && response.results.length > 0) {
                setGroupServices(response.results); // Directly store the paginated data.
                setTotalPages(Math.ceil(response.count / itemsPerPage));
            } else {
                setGroupServices([]); // Handle empty pages.
            }
        } catch (err) {
            console.error("Error fetching data:", err);
            setError("Failed to load data.");
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            setCurrentPage(1); // Reset to page 1 on new search
            fetchGroupServices(searchQuery);
        }
    };

    const handleSearchClick = () => {
        setCurrentPage(1);
        fetchGroupServices(searchQuery);
    };

    const handleDeleteClick = async (serviceId) => {
        try {
            const result = await Swal.fire({
                title: 'Are you sure want to delete ?',
                // text: 'You won’t be able to revert this!',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33',
                confirmButtonText: 'Yes, delete it!',
            });

            if (result.isConfirmed) {
                await deleteGroupServices(serviceId);
                Swal.fire('Deleted!', 'Service has been deleted.', 'success');
                fetchGroupServices();
                setGroupServices((prevServices) =>
                    prevServices.filter((service) => service.id !== serviceId)
                );
            }
        } catch (error) {
            console.error("Error deleting service:", error);
            Swal.fire('Error!', 'Failed to delete the service. Please try again.', 'error');
        }
    };

    const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });

        const sortedServices = [...groupServices].sort((a, b) => {
            if (a[key] < b[key]) return direction === 'asc' ? -1 : 1;
            if (a[key] > b[key]) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        setServices(sortedServices);
    };

    const filteredServices = groupServices.filter((service) =>
        (service.group_name && service.group_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (service.service_count && String(service.service_count).toLowerCase().includes(searchQuery.toLowerCase()))
    );

    const indexOfLastItem = currentPage * itemsPerPage;
    const indexOfFirstItem = indexOfLastItem - itemsPerPage;

    const currentServices = filteredServices;

    if (currentPage === 1 && filteredServices.length > itemsPerPage) {
        const extraItem = filteredServices[filteredServices.length - 1];
        currentServices = [extraItem, ...currentServices.slice(0, itemsPerPage - 1)];
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

    const handleServiceClick = (serviceId) => navigate(`/service-manage/group-services-list/servicedetails/${serviceId}`);
    const handleClientClick = (serviceId) => navigate(`/service-manage/group-services-list/service-details/${serviceId}`);
    const handleEditClick = (serviceId) => navigate(`/service-manage/group-services-list/editgroupservice/${serviceId}`);

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <div className="d-flex justify-content-between align-items-center custom-responsive-style">
                            <div>
                                <H3>Group Services</H3>
                                {/* <span>{"Below is the list of group services along with their details."}</span> */}
                            </div>
                            <div>
                                <button className="btn btn-primary search-btn-clr custom-responsive-style-btn" onClick={() => navigate('/service-manage/add-groupservice')} style={{ marginRight: '20px' }}>
                                    Add Group Service
                                </button>
                                <Input
                                    type="text"
                                    placeholder="Search..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    style={{ width: '200px', display: 'inline-block', marginRight: '10px' }}
                                />
                                <Button className='search-btn-clr' onClick={handleSearchClick}>Search</Button>
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
                                            <th onClick={() => handleSort('group_name')} className='custom-col-design'>Group Service Name
                                                {/* <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" /> */}
                                            </th>
                                            <th onClick={() => handleSort('service_count')} className='custom-col-design'>Service Count
                                                {/* <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" /> */}
                                            </th>
                                            <th className='custom-col-design'>Services</th>
                                            <th className='custom-col-design'>Client Using</th>
                                            <th className='custom-col-design'>Actions</th>
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
                                        ) : currentServices.length === 0 ? (
                                            <tr>
                                                <td colSpan="6" style={{ textAlign: 'center' }}>
                                                    No Group Service Found
                                                </td>
                                            </tr>
                                        ) : (
                                            currentServices.map((service, index) => (
                                                <tr key={index}>
                                                    <td>{indexOfFirstItem + index + 1}</td>
                                                    <td>{service.group_name}</td>
                                                    <td>{service.service_count}</td>
                                                    <td>
                                                        <FaTools
                                                            onClick={() => handleServiceClick(service.id)}
                                                            style={{ cursor: 'pointer' }}
                                                        />
                                                    </td>
                                                    <td>
                                                        <FaTools
                                                            onClick={() => handleClientClick(service.id)}
                                                            style={{ cursor: 'pointer' }}
                                                        />
                                                    </td>
                                                    <td>
                                                        <FaPencilAlt
                                                            color='#6d62e7'
                                                            style={{ cursor: 'pointer', marginRight: '10px' }}
                                                            onClick={() => handleEditClick(service.id)}
                                                        />
                                                        <FaTrashAlt
                                                            color='#ef3636'
                                                            style={{ cursor: 'pointer' }}
                                                            onClick={() => handleDeleteClick(service.id)}
                                                        />
                                                    </td>
                                                </tr>
                                            ))
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

export default GroupService;
