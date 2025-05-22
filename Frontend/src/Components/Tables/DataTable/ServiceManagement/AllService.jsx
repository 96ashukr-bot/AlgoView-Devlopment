import React, { useEffect, useState, Fragment } from 'react';
import {
    Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink,
    Input, Button, Modal, ModalHeader, ModalBody, ModalFooter, FormGroup, Label
} from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import { RotatingLines } from 'react-loader-spinner';
import Swal from 'sweetalert2';
import './ServiceManagement.css'
import { getServices, getSegmentsList, getCategoriesList, createServices, updateServices, deleteServices } from '../../../../Services/Authentication'; // Import the update and delete functions
import { FaArrowUp, FaArrowDown, FaEdit, FaPencilAlt, FaTrashAlt } from 'react-icons/fa';

const AllService = () => {
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);
    const [totalPages, setTotalPages] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('');
    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const [services, setServices] = useState([]);
    const [categories, setCategories] = useState([]);
    const [segments, setSegments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isMobile, setIsMobile] = useState(false);
    const [pageBatch, setPageBatch] = useState(0);
    // Modal state and form fields
    const [modalOpen, setModalOpen] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [currentService, setCurrentService] = useState(null);
    const [newService, setNewService] = useState({
        serviceName: '',
        category: '',
        segment: ''
    });

    useEffect(() => {
        fetchServices(searchQuery);

        const handleResize = () => {
            setIsMobile(window.innerWidth <= 768);
        };

        handleResize();
        window.addEventListener('resize', handleResize);

        return () => window.removeEventListener('resize', handleResize);

    }, [currentPage, itemsPerPage, searchQuery]);

    useEffect(() => {
        fetchCategories();
        fetchSegments();
    }, []);

    const pagesPerBatch = isMobile ? 2 : 4;

    const fetchServices = async (query = '') => {
        try {
            const response = await getServices(currentPage, itemsPerPage, query);
            const sortedServices = response.results.sort((a, b) => b.id - a.id);
            setServices(sortedServices);
            setTotalPages(Math.ceil(response.count / itemsPerPage));
        } catch (err) {
            setLoading(false);
            Swal.fire('Error!', 'Failed to load services.', 'error');
        }
    };

    const fetchSegments = async () => {
        try {
            const data = await getSegmentsList();
            if (Array.isArray(data)) {
                setSegments(data);
            } else if (data.results) {
                setSegments(data.results);
            } else {
                throw new Error('Unexpected response structure');
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const fetchCategories = async () => {
        try {
            const data = await getCategoriesList();
            if (Array.isArray(data)) {
                setCategories(data);
            } else if (data.results) {
                setCategories(data.results);
            } else {
                throw new Error('Unexpected response structure');
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const toggleModal = () => {
        setModalOpen(!modalOpen);
        if (modalOpen) {
            setNewService({ serviceName: '', category: '', segment: '' });
            setIsEditing(false);
            setCurrentService(null);
        }
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setNewService({ ...newService, [name]: value });
    };

    const handleAddService = async () => {
        const serviceData = {
            service_name: newService.serviceName,
            category: parseInt(newService.category),
            segment: parseInt(newService.segment),
        };

        try {
            if (isEditing && currentService) {
                await updateServices(currentService.id, serviceData);
                Swal.fire('Updated!', 'The service has been updated successfully.', 'success');
            } else {
                await createServices(serviceData);
                Swal.fire('Created!', 'A new service has been added.', 'success');
            }
            toggleModal();
            fetchServices();
        } catch (err) {
            Swal.fire('Error!', 'Failed to save the service.', 'error');
        }
    };

    const handleEditService = (service) => {
        setCurrentService(service);
        setNewService({
            serviceName: service.service_name,
            category: service.category.id,
            segment: service.segment.id
        });
        setIsEditing(true);
        toggleModal();
    };

    const handleDeleteService = async (id) => {
        const result = await Swal.fire({
            title: 'Are you sure want to delete ?',
            // text: "You won't be able to revert this!",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Yes',
        });

        if (result.isConfirmed) {
            try {
                await deleteServices(id);
                fetchServices();
                Swal.fire('Deleted!', 'The service has been deleted.', 'success');
            } catch (err) {
                Swal.fire('Error!', 'Failed to delete the service.', 'error');
            }
        }
    };

    const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });

        const sortedServices = [...services].sort((a, b) => {
            if (a[key] < b[key]) return direction === 'asc' ? -1 : 1;
            if (a[key] > b[key]) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        setServices(sortedServices);
    };

    const filteredServices = services.filter(service =>
        ((service.category?.name.toLowerCase().includes(searchQuery.toLowerCase())) ||
            service.service_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            (service.segment?.short_name.toLowerCase().includes(searchQuery.toLowerCase()))) &&
        (selectedCategory === '' || service.category?.name === selectedCategory)
    );

    const indexOfLastService = currentPage * itemsPerPage;
    const indexOfFirstService = indexOfLastService - itemsPerPage;

    let currentServices = filteredServices;

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

    if (loading) return <p>Loading services...</p>;
    if (error) return <p>{error}</p>;

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <div className="d-flex justify-content-between align-items-center custom-responsive-style">
                            <div>
                                <H3>All Services</H3>
                                {/* <span>Below is the list of available services along with their details.</span> */}
                            </div>
                            <div>
                                <Button className='btn btn-primary search-btn-clr custom-responsive-style-btn' style={{ marginRight: '20px' }} onClick={toggleModal}>Add Service</Button>
                                <Input
                                    type="text"
                                    placeholder="Search..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    onKeyPress={(e) => {
                                        if (e.key === 'Enter') {
                                            setCurrentPage(1);
                                            fetchServices(e.target.value);
                                        }
                                    }}
                                    style={{ width: '200px', display: 'inline-block', marginRight: '10px' }}
                                />
                                <Button className="search-btn-clr" onClick={() => {
                                    setCurrentPage(1);
                                    fetchServices(searchQuery);
                                }} >Search</Button>
                            </div>
                        </div>
                    </CardHeader>

                    <div className="card-block row">
                        <Col sm="12">
                            <div className="table-responsive-sm">
                                <Table>
                                    <thead>
                                        <tr>
                                            <th className='custom-col-design'>S.NO</th>
                                            <th onClick={() => handleSort('category')} className='custom-col-design'>
                                                Category <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" />
                                            </th>
                                            <th onClick={() => handleSort('service_name')} className='custom-col-design'>
                                                Service Name <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" />
                                            </th>
                                            <th onClick={() => handleSort('segment')} className='custom-col-design'>
                                                Segment <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" />
                                            </th>
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
                                                <td colSpan="5" style={{ textAlign: 'center' }}>
                                                    No Services Found
                                                </td>
                                            </tr>
                                        ) : (
                                            currentServices.map((service, index) => (
                                                <tr key={service.id}>
                                                    <td>{indexOfFirstService + index + 1}</td>
                                                    <td>{service.category.name}</td>
                                                    <td>{service.service_name}</td>
                                                    <td>{service.segment.short_name}</td>
                                                    <td>
                                                        <FaPencilAlt
                                                            style={{ cursor: 'pointer', marginRight: '10px', color: '#6d62e7' }}
                                                            onClick={() => handleEditService(service)}
                                                        />
                                                        <FaTrashAlt
                                                            style={{ cursor: 'pointer', color: '#dc3545' }}
                                                            onClick={() => handleDeleteService(service.id)}
                                                        />
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </Table>
                            </div>

                            <Pagination className={`d-flex justify-content-end align-items-center ${isMobile ? 'gap-0' : 'gap-0'} custom-pagi-style`}>
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
                        </Col>
                    </div>
                </Card>
            </Col>

            <Modal isOpen={modalOpen} toggle={toggleModal}>
                <ModalHeader toggle={toggleModal}>{isEditing ? 'Edit Service' : 'Add New Service'}</ModalHeader>
                <ModalBody>
                    <FormGroup>
                        <Label for="serviceName">Service Name
                            <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                        </Label>
                        <Input
                            type="text"
                            name="serviceName"
                            id="serviceName"
                            className='custom-input-style'
                            placeholder="Enter Service Name"
                            value={newService.serviceName}
                            onChange={handleInputChange}
                        />
                    </FormGroup>
                    <FormGroup>
                        <Label for="category">Category
                            <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                        </Label>
                        <Input
                            type="select"
                            name="category"
                            id="category"
                            className='custom-input-style'
                            value={newService.category}
                            onChange={handleInputChange}
                        >
                            <option value="">Select Category</option>
                            {categories.map((category) => (
                                <option key={category.id} value={category.id}>{category.name}</option>
                            ))}
                        </Input>
                    </FormGroup>
                    <FormGroup>
                        <Label for="segment">Segment
                            <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                        </Label>
                        <Input
                            type="select"
                            name="segment"
                            id="segment"
                            className='custom-input-style'
                            value={newService.segment}
                            onChange={handleInputChange}
                        >
                            <option value="">Select Segment</option>
                            {segments.map((segment) => (
                                <option key={segment.id} value={segment.id}>{segment.short_name}</option>
                            ))}
                        </Input>
                    </FormGroup>
                </ModalBody>
                <ModalFooter>
                    <Button className='search-btn-clr' onClick={handleAddService}>{isEditing ? 'Update Service' : 'Add Service'}</Button>
                    <Button color="danger" onClick={toggleModal} style={{ marginLeft: '10px' }}>Cancel</Button>
                </ModalFooter>
            </Modal>
        </Fragment>
    );
};

export default AllService;