import React, { Fragment, useEffect, useState } from 'react';
import { Col, Card, Table, CardHeader, Button, Modal, ModalHeader, ModalBody, ModalFooter, Input, FormGroup } from 'reactstrap';
import { H3 } from '../../../AbstractElements';
import { fetchRolesList, createRole, deleteRole } from '../../../Services/Authentication'; 
import { useNavigate } from 'react-router-dom'; 
import { FaEdit, FaTrashAlt } from 'react-icons/fa'; 
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css'; 
import './RolePermission.css';

const RolePermission = () => {
    const [roles, setRoles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [deleteModal, setDeleteModal] = useState(false);
    const [addModal, setAddModal] = useState(false);
    const [roleToDelete, setRoleToDelete] = useState(null);
    const [newRole, setNewRole] = useState({ name: '', status: 'Active' }); 
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
            setNewRole({ name: '', status: 'Active' }); 
            toggleAddModal(); 
            toast.success('New Role Added Successfully.'); 
        } catch (error) {
            console.error('Error adding role:', error);
        }
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
                        <Button color="primary" onClick={toggleAddModal}>Add Role</Button>
                    </CardHeader>
                    <div className="card-block row">
                        <Col sm="12" lg="12" xl="12">
                            <Table className="table-responsive-sm">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Name</th>
                                        <th>Action</th> 
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
                                                    <FaEdit
                                                        className="edit-icon"
                                                        style={{ cursor: 'pointer', marginRight: '10px' }}
                                                        onClick={() => handleEdit(role.id)} 
                                                    />
                                                    <FaTrashAlt
                                                        className="delete-icon"
                                                        style={{ cursor: 'pointer' }}
                                                        onClick={() => handleDelete(role.id)} 
                                                    />
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
                    <Button style={{ backgroundColor: 'orange' }} onClick={toggleDeleteModal}>Cancel</Button>
                    <Button color="primary" onClick={handleDeleteConfirmation}>Delete</Button>
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
                        <h6>Status</h6>
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
                    <Button className='btn-color' onClick={toggleAddModal}>Cancel</Button>
                    <Button color="primary" onClick={handleAddRole}>Add</Button>
                </ModalFooter>
            </Modal>
        </Fragment>
    );
};

export default RolePermission;
