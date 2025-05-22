import React, { Fragment, useEffect, useState } from 'react';
import { Col, Card, Table, CardHeader, Button, Modal, ModalHeader, ModalBody, ModalFooter, Input, FormGroup } from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import { fetchRolesList, createRole, deleteRole } from '../../../../Services/Authentication'; 
import { useNavigate } from 'react-router-dom'; 
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css'; 
import './RolePermission.css';
import { FaEdit, FaTrash, FaArrowUp, FaArrowDown } from 'react-icons/fa';

const RolePermission = () => {
    const [roles, setRoles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [deleteModal, setDeleteModal] = useState(false);
    const [addModal, setAddModal] = useState(false);
    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const [roleToDelete, setRoleToDelete] = useState(null);
    const [newRole, setNewRole] = useState({ name: '', status: 'active' }); 
    const navigate = useNavigate();

    useEffect(() => {
        const getRoles = async () => {
            try {
                const data = await fetchRolesList(); 
                setRoles(data); 
            } catch (error) {
                console.error('Error fetching roles:', error);
            } finally {
                setLoading(false);
            }
        };
        getRoles();
    }, []);

    const handleEdit = (id) => {
        navigate(`/dashboard/rolepermmisionupdate/${id}`);
    };

    const toggleDeleteModal = () => {
        setDeleteModal(!deleteModal);
    };

    const toggleAddModal = () => {
        setAddModal(!addModal);
    };

    const handleDeleteConfirmation = async () => {
        try {
            await deleteRole(roleToDelete); 
            const updatedRoles = roles.filter(role => role.id !== roleToDelete);
            setRoles(updatedRoles);
            toast.success('Role Deleted Successfully.');
        } catch (error) {
            console.error('Error deleting role:', error);
        } finally {
            toggleDeleteModal();
        }
    };

    const handleDelete = (id) => {
        setRoleToDelete(id);
        toggleDeleteModal();
    };

    const handleAddRole = async () => {
        if (newRole.name.trim() === '') {
            toast.error('Role name is required.'); 
            return;
        }
    
        try {
            const response = await createRole(newRole); 
            setRoles([...roles, response]);
            setNewRole({ name: '', status: 'active' }); 
            toggleAddModal(); 
            toast.success('New Role Added Successfully.'); 
        } catch (error) {
            if (error.response && error.response.data.name && error.response.data.name[0] === "role with this name already exists.") {
                toast.error('Role with this name already exists.');
            } else {
                toast.error('Error adding role or Role with this name already exists.');
            }
            console.error('Error adding role:', error);
        }
    };
    
    const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });

        const sortedRoles = [...roles].sort((a, b) => {
            if (a[key] < b[key]) return direction === 'asc' ? -1 : 1;
            if (a[key] > b[key]) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        setRoles(sortedRoles);
    };

    if (loading) {
        return <div>Loading...</div>; 
    }

    return (
        <Fragment>
            <ToastContainer />
            <Col sm="12">
                <Card>
                    <CardHeader className="d-flex justify-content-between align-items-center">
                        <div>
                            <H3>Roles</H3>
                            <span>{"Below is the list of roles along with their details."}</span>
                        </div>
                        <Button className='search-btn-clr' onClick={toggleAddModal}>Add Role</Button>
                    </CardHeader>
                    <div className="card-block row">
                        <Col sm="12" lg="12" xl="12">
                            <Table className="table-responsive-sm">
                                <thead>
                                    <tr>
                                        <th style={{backgroundColor:'#283F7B',color:'white'}}>ID</th>
                                        <th onClick={() => handleSort('name')} style={{ backgroundColor: '#283F7B', color: 'white', cursor: 'pointer', }}>Name <FaArrowUp className="arrow-icon" /> <FaArrowDown  className="arrow-icon"/></th>
                                        <th style={{backgroundColor:'#283F7B',color:'white'}}>Action</th> 
                                    </tr>
                                </thead>
                                <tbody>
                                    {roles.length === 0 ? (
                                        <tr>
                                            <td colSpan="4" className="text-center">No roles available.</td>
                                        </tr>
                                    ) : (
                                        roles.map((role) => (
                                            <tr key={role.id}>
                                                <td>{role.id}</td>
                                                <td>{role.name}</td>
                                                <td>
                                                    <FaEdit color="blue" onClick={() => handleEdit(role.id)} style={{ marginRight: '10px',cursor: 'pointer' }}>
                                                        Edit
                                                    </FaEdit>
                                                    <FaTrash color="red" onClick={() => handleDelete(role.id)} style={{ cursor: 'pointer' }}>
                                                        Delete
                                                    </FaTrash>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </Table>
                        </Col>
                    </div>
                </Card>
            </Col>

            {/* Delete Confirmation Modal */}
            <Modal isOpen={deleteModal} toggle={toggleDeleteModal}>
                <ModalHeader toggle={toggleDeleteModal}>Confirm Deletion</ModalHeader>
                <ModalBody>
                    Are you sure you want to delete this role?
                </ModalBody>
                <ModalFooter>
                    <Button color='primary' onClick={toggleDeleteModal}>Cancel</Button>
                    <Button color="danger" onClick={handleDeleteConfirmation}>Delete</Button>
                </ModalFooter>
            </Modal>

            {/* Add Role Modal */}
            <Modal isOpen={addModal} toggle={toggleAddModal}>
                <ModalHeader toggle={toggleAddModal}>Add New Role</ModalHeader>
                <ModalBody>
                    <FormGroup>
                        <Input
                            type="text"
                            placeholder="Role Name"
                            value={newRole.name}
                            onChange={(e) => setNewRole({ ...newRole, name: e.target.value })}
                        />
                    </FormGroup>
                    <FormGroup>
                        <h6 style={{marginLeft:'4px'}}>Status</h6>
                        <Input
                            type="select"
                            value={newRole.status}
                            onChange={(e) => setNewRole({ ...newRole, status: e.target.value })}
                        >
                            <option value="Active">Active</option>
                            <option value="Inactive">Inactive</option>
                        </Input>
                    </FormGroup>
                </ModalBody>
                <ModalFooter>
                    <Button color='danger' onClick={toggleAddModal}>Cancel</Button>
                    <Button color="primary" onClick={handleAddRole}>Add</Button>
                </ModalFooter>
            </Modal>
        </Fragment>
    );
};

export default RolePermission;
