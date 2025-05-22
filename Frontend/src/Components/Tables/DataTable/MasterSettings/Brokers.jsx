import React, { Fragment, useState, useEffect } from 'react';
import {
    Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink, Button,
    Modal, ModalHeader, ModalBody, Input, FormGroup, Label, FormFeedback, Badge
} from 'reactstrap';
import { RotatingLines } from 'react-loader-spinner';
import { FaEdit, FaTrashAlt, FaArrowUp, FaArrowDown, FaPencilAlt } from 'react-icons/fa';
import Swal from 'sweetalert2';
import { getBroker, addBroker, updateBroker, deleteBroker } from '../../../../Services/Authentication';
import './Settings.css';

const Broker = () => {
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);
    const [brokers, setBrokers] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [editing, setEditing] = useState(false);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);
    const [modalOpen, setModalOpen] = useState(false);
    const [newBroker, setNewBroker] = useState({ id: null, name: '', status: 'Active' });
    const [editIndex, setEditIndex] = useState(null);
    const [errors, setErrors] = useState({});
    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const [isMobile, setIsMobile] = useState(false);
    const [currentGroup, setCurrentGroup] = useState(1);

    useEffect(() => {
        fetchBrokers();

        const handleResize = () => {
            setIsMobile(window.innerWidth <= 768);
        };

        handleResize();
        window.addEventListener('resize', handleResize);

        return () => window.removeEventListener('resize', handleResize);

    }, []);

    const pagesPerGroup = isMobile ? 2 : 4;

    const fetchBrokers = async () => {
        try {
            const data = await getBroker();

            // Format and sort brokers by 'created_at' in descending order
            const formattedBrokers = data.map((broker) => ({
                id: broker.id,
                name: broker.broker_name,
                status: broker.is_active ? 'Active' : 'Inactive',
                createdAt: broker.created_at, // Use this for sorting
            })).sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)); // Sort by created_at descending

            setBrokers(formattedBrokers);
        } catch (error) {
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    const toggleModal = (clearForm = true) => {
        setModalOpen(!modalOpen);
        if (clearForm) resetForm();
    };

    const handleAddOrEditBroker = async () => {
        if (!validateForm()) return;

        try {
            if (editing) {
                const { id, name, status } = newBroker;

                const response = await updateBroker({
                    broker_name: name,
                    is_active: status === 'Active',
                }, id);

                if (response && response.id) {
                    setBrokers(prevBrokers =>
                        prevBrokers.map((broker) =>
                            broker.id === id
                                ? { id: response.id, name: response.broker_name, status: response.is_active ? 'Active' : 'Inactive' }
                                : broker
                        )
                    );
                    Swal.fire('Success', 'Broker updated successfully!', 'success');
                } else {
                    Swal.fire('Error', 'Broker update failed: Invalid response', 'error');
                }
            } else {
                const response = await addBroker({
                    broker_name: newBroker.name,
                    is_active: newBroker.status === 'Active',
                });

                setBrokers(prevBrokers => [
                    { id: response.id, name: response.broker_name, status: response.is_active ? 'Active' : 'Inactive' },
                    ...prevBrokers,
                ]);
                Swal.fire('Success', 'Broker added successfully!', 'success');
            }

            toggleModal();
            resetForm();
        } catch (error) {
            console.error('Error saving broker:', error);
            Swal.fire('Error', 'Failed to save broker', 'error');
        }
    };

    const resetForm = () => {
        setNewBroker({ id: null, name: '', status: 'Active' });
        setEditing(false);
        setEditIndex(null);
        setErrors({});
    };

    const validateForm = () => {
        const newErrors = {};
        if (!newBroker.name.trim()) {
            newErrors.name = 'Broker name is required';
        }
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleEdit = (index) => {
        const broker = brokers[index];
        setNewBroker({
            id: broker.id,
            name: broker.name,
            status: broker.status
        });
        console.log("Editing broker:", { id: broker.id, name: broker.name, status: broker.status });
        setEditing(true);
        setEditIndex(index);
        toggleModal(false);
    };


    const handleDelete = async (index) => {
        const brokerToDelete = brokers[index];
        const brokerId = brokerToDelete.id;

        Swal.fire({
            title: 'Are you sure you want to delete?',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Yes, delete it!',
        }).then(async (result) => {
            if (result.isConfirmed) {
                try {
                    await deleteBroker(brokerId);
                    const updatedBrokers = brokers.filter((_, i) => i !== index);
                    setBrokers(updatedBrokers);
                    Swal.fire('Deleted!', 'The broker has been deleted.', 'success');
                } catch (error) {
                    console.error('Error deleting broker:', error);
                    Swal.fire('Error', 'Failed to delete broker', 'error');
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

        const sortedBrokers = [...brokers].sort((a, b) => {
            if (a[key] < b[key]) return direction === 'asc' ? -1 : 1;
            if (a[key] > b[key]) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        setBrokers(sortedBrokers);
    };

    const filteredBrokers = brokers.filter((broker) =>
        broker.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        broker.status.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const indexOfLastBroker = currentPage * itemsPerPage;
    const indexOfFirstBroker = indexOfLastBroker - itemsPerPage;
    const currentBrokers = filteredBrokers.slice(indexOfFirstBroker, indexOfLastBroker);
    const totalPages = Math.ceil(filteredBrokers.length / itemsPerPage);

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
                    <CardHeader className="d-flex justify-content-between align-items-center custom-responsive-style">
                        <h3>Broker</h3>
                        <div className='custom-style' style={{ marginLeft: '35%' }}>
                            <Button onClick={toggleModal} className="search-btn-clr">
                                Add Broker
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
                                <th className='custom-col-design'>S.NO</th>
                                <th onClick={() => handleSort('name')} className='custom-col-design'>
                                    Name <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" />
                                </th>
                                <th onClick={() => handleSort('status')} className='custom-col-design'>
                                    Status <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" /></th>
                                <th className='custom-col-design'>Action</th>
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
                            ) : currentBrokers.length > 0 ? (
                                currentBrokers.map((broker, index) => (
                                    <tr key={index}>
                                        <td>{indexOfFirstBroker + index + 1}</td>
                                        <td>{broker.name}</td>
                                        <td>
                                            <Badge
                                                pill
                                                className="status-pill"
                                                style={{
                                                    padding: '8px',
                                                    border: `1px solid ${broker.status === 'Active' ? 'green' : 'red'}`,
                                                    color: broker.status === 'Active' ? 'green' : 'red',
                                                    backgroundColor: 'transparent',
                                                }}
                                            >
                                                {broker.status}
                                            </Badge>
                                        </td>
                                        <td>
                                            <FaPencilAlt
                                                onClick={() => handleEdit(indexOfFirstBroker + index)}
                                                style={{ cursor: 'pointer', marginRight: '10px', color: '#6d62e7' }}
                                            />
                                            <FaTrashAlt
                                                onClick={() => handleDelete(indexOfFirstBroker + index)}
                                                style={{ cursor: 'pointer', color: '#dc3545' }}
                                            />
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan="4" style={{ textAlign: 'center', color: 'gray', padding: '10px' }}>
                                        No Broker Found
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </Table>
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
                </Card>
            </Col>
            <Modal isOpen={modalOpen} toggle={toggleModal}>
                <ModalHeader toggle={toggleModal}>{editing ? 'Edit Broker' : 'Add New Broker'}</ModalHeader>
                <ModalBody>
                    <FormGroup>
                        <Label for="brokerName">Broker Name
                            <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                        </Label>
                        <Input
                            id="brokerName"
                            placeholder="Enter broker name"
                            type="text"
                            className='custom-input-style'
                            value={newBroker.name}
                            invalid={!!errors.name}
                            onChange={(e) => setNewBroker({ ...newBroker, name: e.target.value })}
                        />
                        <FormFeedback>{errors.name}</FormFeedback>
                    </FormGroup>
                    <FormGroup>
                        <Label for="brokerStatus">Status
                            <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                        </Label>
                        <Input
                            id="brokerStatus"
                            type="select"
                            className='custom-input-style'
                            value={newBroker.status}
                            onChange={(e) => setNewBroker({ ...newBroker, status: e.target.value })}
                        >
                            <option>Active</option>
                            <option>Inactive</option>
                        </Input>
                    </FormGroup>
                    <div className="d-flex justify-content-end">
                        <Button onClick={handleAddOrEditBroker} className='search-btn-clr'>
                            {editing ? 'Update' : 'Add Broker'}
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

export default Broker;
