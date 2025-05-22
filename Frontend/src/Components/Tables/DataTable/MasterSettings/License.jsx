import React, { Fragment, useState, useEffect } from 'react';
import {
    Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink, Button, Input,
    FormGroup, Label, FormFeedback, Modal, ModalHeader, ModalBody, ModalFooter
} from 'reactstrap';
import { FaEdit, FaTrashAlt, FaArrowUp, FaArrowDown } from 'react-icons/fa';
import Swal from 'sweetalert2';
import { getLicence, addLicense, updateLicense, deleteLicense } from '../../../../Services/Authentication';

const License = () => {
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage] = useState(10);
    const [licenses, setLicenses] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [editing, setEditing] = useState(false);
    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const [error, setError] = useState(null);
    const [newLicense, setNewLicense] = useState({ name: '', no_of_days_month: '', period: '', status: 'true' });
    const [editIndex, setEditIndex] = useState(null);
    const [errors, setErrors] = useState({});
    const [isModalOpen, setIsModalOpen] = useState(false); // Modal state

    // Fetch licenses on component mount
    useEffect(() => {
        getlicence();
    }, []);

    const getlicence = async () => {
        try {
            const data = await getLicence();
            const sortedLicenses = data.results.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            setLicenses(sortedLicenses);
        } catch (err) {
            setError(err.message);
        }
    };

    const updateLocalStorage = (updatedLicenses) => {
        localStorage.setItem('licenses', JSON.stringify(updatedLicenses));
    };

    const toggleModal = () => setIsModalOpen(!isModalOpen);

    const handleAddOrEditLicense = async (event) => {
        event.preventDefault();
        if (!validateForm()) return;

        try {
            const licenseToAdd = {
                ...newLicense,
                status: newLicense.status === 'true' || newLicense.status === true,
            };

            if (editing) {
                await updateLicense(licenseToAdd, newLicense.id);
                setLicenses((prev) => prev.map((license) =>
                    license.id === newLicense.id ? { ...license, ...licenseToAdd } : license
                ));
            } else {
                const addedLicense = await addLicense(licenseToAdd);
                setLicenses((prev) => [addedLicense, ...prev]);
            }

            resetForm();
            toggleModal();
        } catch (error) {
            console.error('Error adding/updating license:', error);
            Swal.fire('Error', 'Failed to add/update license. Please try again.', 'error');
        }
    };

    const handleDelete = async (index) => {
        const licenceToDelete = licenses[index];
        console.log('Deleting license:', licenceToDelete);

        Swal.fire({
            title: `Are you sure you want to delete ${licenceToDelete.name}?`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Yes, delete it!',
        }).then(async (result) => {
            if (result.isConfirmed) {
                try {
                    const message = await deleteLicense(licenceToDelete.id);
                    //   console.log(licenceToDelete.id);

                    const filteredsegments = licenses.filter((_, i) => i !== index);
                    setLicenses(filteredsegments);
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

        const sortedLicense = [...licenses].sort((a, b) => {
            if (a[key] < b[key]) return direction === 'asc' ? -1 : 1;
            if (a[key] > b[key]) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        setLicenses(sortedLicense);
    };

    const resetForm = () => {
        setNewLicense({ name: '', no_of_days_month: '', period: '', status: 'true' });
        setEditing(false);
        setEditIndex(null);
        setErrors({});
    };

    const validateForm = () => {
        const newErrors = {};
        if (!newLicense.name.trim()) newErrors.name = 'Name is required';
        if (!newLicense.no_of_days_month) newErrors.no_of_days_month = 'Valid To is required';
        if (!newLicense.period) newErrors.period = 'Period is required';
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleEdit = (index) => {
        setNewLicense({ ...licenses[index] });
        setEditing(true);
        setEditIndex(index);
        toggleModal();
    };

    const filteredLicenses = licenses.filter((license) =>
        license.name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    useEffect(() => {
        setCurrentPage(1);
    }, [licenses]);

    console.log(setCurrentPage);

    const indexOfLastLicense = currentPage * itemsPerPage;
    const indexOfFirstLicense = indexOfLastLicense - itemsPerPage;
    const currentLicenses = filteredLicenses.slice(indexOfFirstLicense, indexOfLastLicense);
    const totalPages = Math.ceil(filteredLicenses.length / itemsPerPage);

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader className="d-flex justify-content-between align-items-center">
                        <h3>License</h3>
                        <Button style={{marginLeft:'50%'}} className="search-btn-clr" onClick={() => { resetForm(); toggleModal(); }}>
                            Add License
                        </Button>
                        <div className="d-flex align-items-center">
                            <Input
                                type="text"
                                placeholder="Search..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                style={{ width: '200px', marginRight: '10px' }}
                            />
                            <Button className="search-btn-clr">Search</Button>
                        </div>
                    </CardHeader>

                    <Table responsive>
                        <thead>
                            <tr>
                                <th style={{ backgroundColor: '#283F7B', color: 'white' }}>S.No</th>
                                <th onClick={() => handleSort('name')} style={{ backgroundColor: '#283F7B', color: 'white', cursor: 'pointer', }}>
                                    Name <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" />
                                </th>
                                <th onClick={() => handleSort('no_of_days_month')} style={{ backgroundColor: '#283F7B', color: 'white', cursor: 'pointer', }}>
                                    Valid To <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" />
                                </th>
                                <th onClick={() => handleSort('period')} style={{ backgroundColor: '#283F7B', color: 'white', cursor: 'pointer', }}>
                                    Period <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" /></th>
                                <th onClick={() => handleSort('status')} style={{ backgroundColor: '#283F7B', color: 'white', cursor: 'pointer', }}>
                                    Status <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" /></th>
                                <th style={{ backgroundColor: '#283F7B', color: 'white' }}>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {currentLicenses.map((license, index) => (
                                <tr key={index}>
                                    <td>{indexOfFirstLicense + index + 1}</td>
                                    <td>{license.name}</td>
                                    <td>{license.no_of_days_month}</td>
                                    <td>{license.period}</td>
                                    <td>{license.status ? 'Active' : 'Inactive'}</td>
                                    <td>
                                        <FaEdit
                                            style={{ cursor: 'pointer', marginRight: '10px', color: 'blue' }}
                                            onClick={() => handleEdit(indexOfFirstLicense + index)}
                                        />
                                        <FaTrashAlt
                                            style={{ cursor: 'pointer', color: '#dc3545' }}
                                            onClick={() => handleDelete(licenses.indexOf(license))}
                                        />
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </Table>
                </Card>
                <Pagination className="d-flex justify-content-end custom-pagi-style">
                    <PaginationItem disabled={currentPage === 1}>
                        <PaginationLink onClick={() => setCurrentPage(currentPage - 1)}>
                            Previous
                        </PaginationLink>
                    </PaginationItem>
                    {[...Array(totalPages)].map((_, index) => (
                        <PaginationItem key={index} active={index + 1 === currentPage}>
                            <PaginationLink onClick={() => setCurrentPage(index + 1)}>
                                {index + 1}
                            </PaginationLink>
                        </PaginationItem>
                    ))}
                    <PaginationItem disabled={currentPage === totalPages}>
                        <PaginationLink onClick={() => setCurrentPage(currentPage + 1)}>
                            Next
                        </PaginationLink>
                    </PaginationItem>
                </Pagination>
            </Col>

            {/* Modal */}
            <Modal isOpen={isModalOpen} toggle={toggleModal}>
                <ModalHeader toggle={toggleModal}>{editing ? 'Edit License' : 'Add New License'}</ModalHeader>
                <ModalBody>
                    <FormGroup>
                        <Label>Name</Label>
                        <Input
                            type="text"
                            placeholder="Enter name"
                            value={newLicense.name}
                            invalid={!!errors.name}
                            onChange={(e) => setNewLicense({ ...newLicense, name: e.target.value })}
                        />
                        <FormFeedback>{errors.name}</FormFeedback>
                    </FormGroup>

                    <FormGroup>
                        <Label>Valid To</Label>
                        <Input
                            type="number"
                            value={newLicense.no_of_days_month}
                            min={1}
                            placeholder="Enter a number"
                            onChange={(e) => setNewLicense({ ...newLicense, no_of_days_month: e.target.value })}
                        />
                        <FormFeedback>{errors.no_of_days_month}</FormFeedback>
                    </FormGroup>

                    <FormGroup>
                        <Label>Period</Label>
                        <Input
                            type="select"
                            value={newLicense.period}
                            onChange={(e) => setNewLicense({ ...newLicense, period: e.target.value })}
                        >
                            <option value="">Select Period</option>
                            <option value="January">January</option>
                            <option value="February">February</option>
                            <option value="March">March</option>
                            <option value="April">April</option>
                        </Input>
                    </FormGroup>

                    <FormGroup>
                        <Label>Status</Label>
                        <Input
                            type="select"
                            value={newLicense.status}
                            onChange={(e) => setNewLicense({ ...newLicense, status: e.target.value })}
                        >
                            <option value="true">Active</option>
                            <option value="false">Inactive</option>
                        </Input>
                    </FormGroup>
                </ModalBody>
                <ModalFooter>
                    <Button className="search-btn-clr" onClick={handleAddOrEditLicense}>
                        {editing ? 'Update' : 'Add'}
                    </Button>
                    <Button color="danger" onClick={toggleModal}>Cancel</Button>
                </ModalFooter>
            </Modal>
        </Fragment>
    );
};

export default License;
