import React, { Fragment, useState, useEffect } from 'react';
import {
    Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink,
    Button, Modal, ModalHeader, ModalBody, Input, FormGroup, Label, FormFeedback, Badge
} from 'reactstrap';
import { FaTrashAlt, FaArrowUp, FaArrowDown, FaPencilAlt } from 'react-icons/fa';
import Swal from 'sweetalert2';
import { RotatingLines } from 'react-loader-spinner';
import './Settings.css';
import { getServices, createServices, getSegmentsList, getCategoriesList, updateServices, deleteServices } from '../../../../Services/Authentication';

const Services = () => {
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);
    const [totalPages, setTotalPages] = useState([]);
    const [services, setServices] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [editing, setEditing] = useState(false);
    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const [modalOpen, setModalOpen] = useState(false);
    const [newService, setNewService] = useState({
        id: null,
        name: '',
        category: '',
        segment: '',
        status: true,
    });
    const [editIndex, setEditIndex] = useState(null);
    const [errors, setErrors] = useState({});
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);
    const [isMobile, setIsMobile] = useState(false);
    const [pageBatch, setPageBatch] = useState(0);
    const [segments, setSegments] = useState([]);
    const [categories, setCategories] = useState([]);

    useEffect(() => {
        fetchServices();

        const handleResize = () => {
            setIsMobile(window.innerWidth <= 768);
        };

        handleResize();
        window.addEventListener('resize', handleResize);

        return () => window.removeEventListener('resize', handleResize);

    }, [currentPage, itemsPerPage]);

    useEffect(() => {
        // fetchServices();
        fetchSegments();
        fetchCategories();
    }, []);

    const pagesPerBatch = isMobile ? 2 : 4;

    const fetchServices = async () => {
        try {
            const response = await getServices(currentPage, itemsPerPage);
            const mappedServices = (response.results || []).map((service) => ({
                id: service.id,
                name: service.service_name,
                category: service.category.name,
                segment: service.segment.name,
                status: service.status ? 'Active' : 'Inactive',
                created_at: new Date(service.created_at),
            }));

            // Sort services by creation date in descending order
            mappedServices.sort((a, b) => b.created_at - a.created_at);

            console.log('Mapped Services:', mappedServices);
            setServices(mappedServices);
            setTotalPages(Math.ceil(response.count / itemsPerPage));
        } catch (error) {
            console.error('Error fetching services:', error);
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

    const toggleModal = (clearForm = true) => {
        setModalOpen(!modalOpen);
        if (clearForm) resetForm();
    };

    const updateLocalStorage = (services) => {
        localStorage.setItem('services', JSON.stringify(services));
    };

    const handleAddOrEditService = async () => {
        if (!validateForm()) return;

        console.log('New Service ID:', newService.id);

        try {
            if (editing) {
                const response = await updateServices(newService.id, {
                    service_name: newService.name,
                    category: newService.category,
                    segment: newService.segment,
                    status: newService.status === 'Active',
                });

                const updatedService = response.data;
                const updatedServices = [...services];
                updatedServices[editIndex] = {
                    id: updatedService.id,
                    name: updatedService.service_name,
                    category: updatedService.category.name,
                    segment: updatedService.segment.name,
                    status: updatedService.status ? 'Active' : 'Inactive',
                };

                setServices(updatedServices);
                updateLocalStorage(updatedServices);

                Swal.fire('Updated!', 'Service updated successfully.', 'success');
                fetchServices();
            } else {
                const response = await createServices({
                    service_name: newService.name,
                    category: newService.category,
                    segment: newService.segment,
                    status: newService.status === 'Active',
                });

                const createdService = response.data;

                // Add the new service at the beginning of the array
                const updatedServices = [
                    {
                        id: createdService.id,
                        name: createdService.service_name,
                        category: createdService.category.name,
                        segment: createdService.segment.name,
                        status: createdService.status ? 'Active' : 'Inactive',
                    },
                    ...services,
                ];

                setServices(updatedServices);
                updateLocalStorage(updatedServices);

                Swal.fire('Created!', 'Service created successfully.', 'success');
                fetchServices();
            }
            resetForm();
            toggleModal();
        } catch (error) {
            console.error('Error creating or updating service:', error);
            Swal.fire('Error!', 'Something went wrong. Please try again.', 'error');
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

    const resetForm = () => {
        setNewService({ name: '', category: '', segment: '', status: true });
        setEditing(false);
        setEditIndex(null);
        setErrors({});
    };

    const validateForm = () => {
        const newErrors = {};
        if (!newService.name.trim()) newErrors.name = 'Name is required';
        if (!newService.category) newErrors.category = 'Category is required';
        if (!newService.segment) newErrors.segment = 'Segment is required';
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleEdit = (index) => {
        const selectedService = services[index];
        console.log('Editing Service:', selectedService);

        const category = categories.find((cat) => cat.name === selectedService.category);
        const segment = segments.find((seg) => seg.name === selectedService.segment);

        setNewService({
            id: selectedService.id,
            name: selectedService.name,
            category: category ? category.id : '',
            segment: segment ? segment.id : '',
            status: selectedService.status === 'Active', // Map 'Active' to true and 'Inactive' to false
        });
        setEditing(true);
        setEditIndex(index);
        toggleModal(false);
    };


    const handleDelete = async (index) => {
        const serviceToDelete = services[index];

        Swal.fire({
            title: `Are you sure you want to delete ${serviceToDelete.name}?`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Yes, delete it!',
        }).then(async (result) => {
            if (result.isConfirmed) {
                try {
                    const message = await deleteServices(serviceToDelete.id);
                    console.log(message);

                    const filteredServices = services.filter((_, i) => i !== index);
                    setServices(filteredServices);
                    updateLocalStorage(filteredServices);

                    Swal.fire('Deleted!', message, 'success');
                } catch (error) {
                    console.error('Error deleting service:', error.message);
                    Swal.fire('Error!', error.message, 'error');
                }
            }
        });
    };


    const filteredServices = services.filter((service) =>
        service.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        service.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
        service.segment.toLowerCase().includes(searchQuery.toLowerCase()) ||
        service.status.toLowerCase().includes(searchQuery.toLowerCase())
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


    if (loading) return <p>Loading segments...</p>;
    if (error) return <p>Error: {error}</p>;

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader className="d-flex justify-content-between align-items-center custom-responsive-style">
                        <h3>Services</h3>
                        <div className='custom-style' style={{ marginLeft: '35%' }}>
                            <Button onClick={toggleModal} className="search-btn-clr">
                                Add Service
                            </Button>
                        </div>
                        <div className="custom-responsive-style-btns" style={{ display: 'flex' }}>
                            <Input
                                type="text"
                                placeholder="Search..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className='custom-input-styles'
                            />
                            <Button className="search-btn-clr text-nowrap">Search</Button>
                        </div>
                    </CardHeader>
                    <Table responsive>
                        <thead>
                            <tr>
                                <th className='custom-col-design'>S.No.</th>
                                <th onClick={() => handleSort('name')} className='custom-col-design'>
                                    Service Name <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" /></th>
                                <th onClick={() => handleSort('category')} className='custom-col-design'>Category <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" /></th>
                                <th onClick={() => handleSort('segment')} className='custom-col-design'>Segment <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" /></th>
                                <th onClick={() => handleSort('status')} className='custom-col-design' >Status <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" /></th>
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
                            ) : currentServices.length > 0 ? (
                                currentServices.map((service, index) => (
                                    <tr key={service.id}>
                                        <td>{index + 1}</td>
                                        <td>{service.name}</td>
                                        <td>{service.category}</td>
                                        <td>{service.segment}</td>
                                        <td>
                                            <Badge
                                                pill
                                                className="status-pill"
                                                style={{
                                                    padding: '8px',
                                                    border: service.status === 'Active' ? '1px solid green' : '1px solid red',
                                                    color: service.status === 'Active' ? 'green' : 'red',
                                                    backgroundColor: service.status === 'Active' ? 'transparent' : 'lightcoral',
                                                }}
                                            >
                                                {service.status}
                                            </Badge>
                                        </td>
                                        <td>
                                            <FaPencilAlt
                                                style={{ cursor: 'pointer', marginRight: '10px', color: '#6d62e7' }}
                                                onClick={() => handleEdit(indexOfFirstService + index)}
                                            />
                                            <FaTrashAlt
                                                style={{ cursor: 'pointer', color: '#dc3545' }}
                                                onClick={() => handleDelete(indexOfFirstService + index)}
                                            />
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan="6" style={{ textAlign: 'center', padding: '20px' }}>
                                        No Service Found
                                    </td>
                                </tr>
                            )}
                        </tbody>


                    </Table>

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
                </Card>
            </Col>
            <Modal isOpen={modalOpen} toggle={toggleModal}>
                <ModalHeader toggle={toggleModal}>
                    {editing ? 'Edit Service' : 'Add Service'}
                </ModalHeader>
                <ModalBody>
                    <FormGroup>
                        <Label for="name">Service Name
                            <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                        </Label>
                        <Input
                            type="text"
                            placeholder='Enter Service Name'
                            className='custom-input-style'
                            id="name"
                            value={newService.name}
                            onChange={(e) => setNewService({ ...newService, name: e.target.value })}
                            invalid={!!errors.name}
                        />
                        <FormFeedback>{errors.name}</FormFeedback>
                    </FormGroup>

                    <FormGroup>
                        <Label for="category">Category
                            <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                        </Label>
                        <Input
                            type="select"
                            id="category"
                            className='custom-input-style'
                            value={newService.category}
                            onChange={(e) => setNewService({ ...newService, category: e.target.value })}
                            invalid={!!errors.category}
                        >
                            <option value="">Select a category</option>
                            {categories.map((cat) => (
                                <option key={cat.id} value={cat.id}>
                                    {cat.name}
                                </option>
                            ))}
                        </Input>
                        <FormFeedback>{errors.category}</FormFeedback>
                    </FormGroup>

                    <FormGroup>
                        <Label for="segment">Segment
                            <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                        </Label>
                        <Input
                            type="select"
                            id="segment"
                            className='custom-input-style'
                            value={newService.segment}
                            onChange={(e) => setNewService({ ...newService, segment: e.target.value })}
                            invalid={!!errors.segment}
                        >
                            <option value="">Select a segment</option>
                            {segments.map((seg) => (
                                <option key={seg.id} value={seg.id}>
                                    {seg.name}
                                </option>
                            ))}
                        </Input>
                        <FormFeedback>{errors.segment}</FormFeedback>
                    </FormGroup>


                    <FormGroup>
                        <Label for="categoryStatus">Status
                            <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                        </Label>
                        <Input
                            id="serviceStatus"
                            type="select"
                            className='custom-input-style'
                            value={newService.status}
                            onChange={(e) =>
                                setNewService({ ...newService, status: e.target.value })
                            }
                        >
                            <option value="">Select Status</option>
                            <option value="Active">Active</option>
                            <option value="Inactive">Inactive</option>
                        </Input>
                    </FormGroup>

                    <div className="d-flex justify-content-end">
                        <Button className='search-btn-clr' onClick={handleAddOrEditService}>
                            {editing ? 'Update' : 'Add Service'}
                        </Button>
                        <Button
                            color="danger"
                            onClick={toggleModal}
                            style={{ marginLeft: '10px' }}
                        >
                            Cancel
                        </Button>
                    </div>
                </ModalBody>
            </Modal>

        </Fragment>
    );
};

export default Services;

