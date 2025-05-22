import React, { Fragment, useState, useEffect } from 'react';
import {
    Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink, Button, Modal, ModalHeader, ModalBody, Input, FormGroup, Label, FormFeedback, Badge
} from 'reactstrap';
import { FaEdit, FaTrashAlt, FaArrowUp, FaArrowDown, FaPencilAlt } from 'react-icons/fa';
import Swal from 'sweetalert2';
import { RotatingLines } from 'react-loader-spinner';
import {
    getSegments,
    createSegment,
    updateSegment,
    deleteSegment
} from '../../../../Services/Authentication';
import './Settings.css';

const Segment = () => {
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);
    const [totalPages, setTotalPages] = useState([]);
    const [segments, setSegments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const [editing, setEditing] = useState(false);
    const [modalOpen, setModalOpen] = useState(false);
    const [newSegment, setNewSegment] = useState({
        id: null,
        name: '',
        short_name: '',
        status: true,
    });
    const [editIndex, setEditIndex] = useState(null);
    const [errors, setErrors] = useState({});
    const [isMobile, setIsMobile] = useState(false);
    const [pageBatch, setPageBatch] = useState(0);

    useEffect(() => {
        fetchSegments();

        const handleResize = () => {
            setIsMobile(window.innerWidth <= 768);
        };

        handleResize();
        window.addEventListener('resize', handleResize);

        return () => window.removeEventListener('resize', handleResize);

    }, [currentPage, itemsPerPage]);

    const pagesPerBatch = isMobile ? 2 : 4;

    const fetchSegments = async () => {
        try {
            const data = await getSegments(currentPage, itemsPerPage);
            const sortedSegments = data.results.sort((a, b) => b.id - a.id);
            setSegments(sortedSegments);
            setTotalPages(Math.ceil(data.count / itemsPerPage));
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

    const updateLocalStorage = (segments) => {
        localStorage.setItem('segments', JSON.stringify(segments));
    };

    const handleAddOrEditSegment = async () => {
        if (!validateForm()) return;

        try {
            if (editing) {
                await updateSegment(newSegment, newSegment.id);
                const updatedSegments = [...segments];
                updatedSegments[editIndex] = newSegment;
                setSegments(updatedSegments);
                Swal.fire('Success', 'Segment updated successfully!', 'success');
            } else {
                const response = await createSegment(newSegment);
                // Add the new segment at the start of the array
                setSegments([response, ...segments]);
                Swal.fire('Success', 'Segment created successfully!', 'success');
                fetchSegments();
            }
            resetForm();
            toggleModal();
        } catch (err) {
            console.error('Error:', err);
            Swal.fire('Error', 'Failed to save the segment.', 'error');
            fetchSegments();
        }
    };


    const resetForm = () => {
        setNewSegment({ id: null, name: '', short_name: '', status: true });
        setEditing(false);
        setEditIndex(null);
        setErrors({});
    };

    const validateForm = () => {
        const newErrors = {};
        if (!newSegment.name.trim()) newErrors.name = 'Segment name is required';
        if (!newSegment.short_name.trim()) newErrors.short_name = 'Short name is required';
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleEdit = (index) => {
        const segmentToEdit = segments[index];
        setNewSegment({ ...segmentToEdit });
        setEditing(true);
        setEditIndex(index);
        toggleModal(false);
    };

    const handleDelete = async (index) => {
        const segmentsToDelete = segments[index];

        Swal.fire({
            title: `Are you sure you want to delete ${segmentsToDelete.name}?`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Yes, delete it!',
        }).then(async (result) => {
            if (result.isConfirmed) {
                try {
                    const message = await deleteSegment(segmentsToDelete.id);
                    console.log(message);

                    const filteredsegments = segments.filter((_, i) => i !== index);
                    setSegments(filteredsegments);
                    updateLocalStorage(filteredsegments);

                    Swal.fire('Deleted!', message, 'success');
                } catch (error) {
                    console.error('Error deleting service:', error.message);
                    Swal.fire('Error!', error.message, 'error');
                }
            }
        });
    };

    const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });

        const sortedSegments = [...segments].sort((a, b) => {
            if (a[key] < b[key]) return direction === 'asc' ? -1 : 1;
            if (a[key] > b[key]) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        setSegments(sortedSegments);
    };

    const filteredSegments = segments.filter((segment) => {
        const statusText = segment.status ? 'active' : 'inactive';
        return (
            segment.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            segment.short_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            statusText.includes(searchQuery.toLowerCase())
        );
    });

    const indexOfLastSegment = currentPage * itemsPerPage;
    const indexOfFirstSegment = indexOfLastSegment - itemsPerPage;

    let currentSegments = filteredSegments;

    if (currentPage === 1 && filteredSegments.length > itemsPerPage) {
        const extraItem = filteredSegments[filteredSegments.length - 1];
        currentSegments = [extraItem, ...currentSegments.slice(0, itemsPerPage - 1)];
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

    if (error) return <p>Error: {error}</p>;

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader className="d-flex justify-content-between align-items-center custom-responsive-style">
                        <h3>Segment</h3>
                        <div className='custom-style' style={{ marginLeft: '35%' }}>
                            <Button onClick={toggleModal} className="search-btn-clr">
                                Add Segment
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
                    <div className="card-block row">
                        <Col sm="12" lg="12" xl="12" >
                            <div className="table-responsive-sm">
                                <Table responsive>
                                    <thead>
                                        <tr>
                                            <th className='custom-col-design' >S.No.</th>
                                            <th onClick={() => handleSort('name')} className='custom-col-design' >Segment Name <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" /></th>
                                            <th onClick={() => handleSort('short_name')} className='custom-col-design' >Short Name <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" /></th>
                                            <th onClick={() => handleSort('status')} className='custom-col-design' >Status <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" /></th>
                                            <th className='custom-col-design' >Action</th>
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
                                        ) : currentSegments.length > 0 ? (
                                            currentSegments.map((segment, index) => (
                                                <tr key={index}>
                                                    <td>{(currentPage - 1) * itemsPerPage + index + 1}</td>
                                                    <td>{segment.name}</td>
                                                    <td>{segment.short_name}</td>
                                                    <td>
                                                        <Badge
                                                            pill
                                                            className="status-pill"
                                                            style={{
                                                                padding: '8px',
                                                                border: `1px solid ${segment.status ? 'green' : 'red'}`,
                                                                color: segment.status ? 'green' : 'red',
                                                                backgroundColor: 'transparent',
                                                            }}
                                                        >
                                                            {segment.status ? 'Active' : 'Inactive'}
                                                        </Badge>
                                                    </td>
                                                    <td>
                                                        <FaPencilAlt
                                                            style={{ cursor: 'pointer', color: '#6d62e7', marginRight: '10px' }}
                                                            onClick={() =>
                                                                handleEdit(indexOfFirstSegment + index)
                                                            }
                                                        />
                                                        <FaTrashAlt
                                                            style={{ cursor: 'pointer', color: '#dc3545' }}
                                                            onClick={() =>
                                                                handleDelete(indexOfFirstSegment + index)
                                                            }
                                                        />
                                                    </td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan="5" style={{ textAlign: 'center', padding: '20px', }}>
                                                    No Segments Found
                                                </td>
                                            </tr>
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
                <ModalHeader toggle={toggleModal}>
                    {editing ? 'Edit Segment' : 'Add New Segment'}
                </ModalHeader>
                <ModalBody>
                    <FormGroup>
                        <Label>Segment Name
                            <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                        </Label>
                        <Input
                            placeholder='Enter Segment Name'
                            type="text"
                            className='custom-input-style'
                            value={newSegment.name}
                            invalid={!!errors.name}
                            onChange={(e) => setNewSegment({ ...newSegment, name: e.target.value })}
                        />
                        <FormFeedback>{errors.name}</FormFeedback>
                    </FormGroup>
                    <FormGroup>
                        <Label>Short Name
                            <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                        </Label>
                        <Input
                            placeholder='Enter Short Name'
                            type="text"
                            className='custom-input-style'
                            value={newSegment.short_name}
                            invalid={!!errors.short_name}
                            onChange={(e) =>
                                setNewSegment({ ...newSegment, short_name: e.target.value })
                            }
                        />
                        <FormFeedback>{errors.short_name}</FormFeedback>
                    </FormGroup>
                    <FormGroup>
                        <Label>Status
                            <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                        </Label>
                        <Input
                            type="select"
                            className='custom-input-style'
                            value={newSegment.status ? 'Active' : 'Inactive'}
                            onChange={(e) =>
                                setNewSegment({ ...newSegment, status: e.target.value === 'Active' })
                            }
                        >
                            <option>Active</option>
                            <option>Inactive</option>
                        </Input>
                    </FormGroup>
                    <div className="d-flex justify-content-end">
                        <Button className="search-btn-clr" onClick={handleAddOrEditSegment}>
                            {editing ? 'Update' : 'Add'}
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

export default Segment;
