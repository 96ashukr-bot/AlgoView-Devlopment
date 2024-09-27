import React, { Fragment, useEffect, useState } from 'react';
import { Col, Card, Table, CardHeader } from 'reactstrap';
import { H3 } from '../../../AbstractElements';
import { fetchRolesList } from '../../../Services/Authentication';
import { useNavigate } from 'react-router-dom'; 
import { FaEdit, FaTrashAlt } from 'react-icons/fa'; 
import './RolePermission.css';

const RolePermission = () => {
    const [roles, setRoles] = useState([]);
    const navigate = useNavigate();

    useEffect(() => {
        const getRoles = async () => {
            try {
                const data = await fetchRolesList(); 
                setRoles(data); 
            } catch (error) {
                console.error('Error fetching roles:', error);
            }
        };
        getRoles();
    }, []);

    const handleEdit = (id) => {
        navigate(`/dashboard/rolepermmisionupdate/${id}`);
    };

    const handleDelete = (id) => {
        const updatedRoles = roles.filter(role => role.id !== id);
        setRoles(updatedRoles);
    };

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <H3>Roles</H3>
                        <span>{"Below is the list of roles along with their details."}</span>
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
                                    {roles.map((role) => (
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
                                    ))}
                                </tbody>
                            </Table>
                        </Col>
                    </div>
                </Card>
            </Col>
        </Fragment>
    );
};

export default RolePermission;
