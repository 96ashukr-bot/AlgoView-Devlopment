import React, { Fragment, useEffect, useState } from 'react';
import { Col, Card, Table, CardHeader, Button } from 'reactstrap';
import { H3 } from '../../../AbstractElements';
import { fetchRolePermissions, updateRolePermissions } from '../../../Services/Authentication';
import { useParams } from 'react-router-dom';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const RolePermissionUpdate = () => {
    const { layout } = useParams();
    const [permissions, setPermissions] = useState({});
    const [allPermissions, setAllPermissions] = useState([]);
    const [selectedRole, setSelectedRole] = useState(null);

    useEffect(() => {
        const getPermissions = async () => {
            try {
                const data = await fetchRolePermissions();
                console.log("Fetched permissions data:", data);
                extractPermissions(data);
            } catch (error) {
                console.error('Error fetching permissions:', error);
            }
        };

        getPermissions();
    }, []);

    const extractPermissions = (data) => {
        setAllPermissions(data);
        const selectedRoleData = data.find(roleData => roleData.role.id.toString() === layout);
        setSelectedRole(selectedRoleData);

        if (selectedRoleData) {
            const updatedPermissions = {};
            selectedRoleData.permissions.forEach(permission => {
                const permissionArray = permission.permission.split(', ').map(perm => perm.trim());
                permissionArray.forEach(perm => {
                    if (!updatedPermissions[permission.group]) {
                        updatedPermissions[permission.group] = { create: false, read: false, update: false, delete: false };
                    }
                    updatedPermissions[permission.group][perm] = true;
                });
            });
            setPermissions(updatedPermissions);
        } else {
            console.warn(`No permissions found for role ID: ${layout}`);
            setPermissions({});
        }
    };


    const handleCheckboxChange = (group, perm) => {
        setPermissions(prevPermissions => ({
            ...prevPermissions,
            [group]: {
                ...prevPermissions[group],
                [perm]: !prevPermissions[group]?.[perm],
            },
        }));
    };

    const handleSave = async () => {
        console.log('handlesave',handleSave);
        
        if (selectedRole) {
            console.log('selectedRole',selectedRole);

            try {
                const roleId = selectedRole.role.id;
                console.log("Saving permissions for role:", roleId, permissions);

                const response = await updateRolePermissions(roleId, permissions);
                console.log("Permissions updated successfully:", response);

                toast.success("Permissions updated successfully!");
            } catch (error) {
                console.error("Error saving permissions:", error);
                toast.error("Failed to update permissions. Please try again.");
            }
        }
    };

    return (
        <Fragment>
            <Card>
                <CardHeader>
                    <H3>Role & Permission</H3>
                    <span>Below is the list of roles & permissions along with their details.</span>
                </CardHeader>
                <Col>
                    {allPermissions && selectedRole ? (
                        <div key={selectedRole.role.id}>
                            <CardHeader>
                                <h5>{selectedRole.role.name.charAt(0).toUpperCase() + selectedRole.role.name.slice(1)}</h5>
                                <span>Below is the list of roles & permissions of {selectedRole.role.name.charAt(0).toUpperCase() + selectedRole.role.name.slice(1)}.</span>
                            </CardHeader>
                            <div className="table-responsive" style={{ overflow: 'visible' }}>
                                <Table className="table-responsive-sm" style={{ width: '100%' }}>
                                    <thead>
                                        <tr>
                                            <th>Name</th>
                                            <th>Create</th>
                                            <th>Read</th>
                                            <th>Update</th>
                                            <th>Delete</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {selectedRole.permissions.map((perm, index) => (
                                            <tr key={`${perm.group}-${perm.permission}-${index}`}>
                                                <td>{perm.group}</td>
                                                <td>
                                                    <input
                                                        type="checkbox"
                                                        checked={permissions[perm.group]?.create || false}
                                                        onChange={() => handleCheckboxChange(perm.group, 'create')}
                                                    />
                                                </td>
                                                <td>
                                                    <input
                                                        type="checkbox"
                                                        checked={permissions[perm.group]?.read || false}
                                                        onChange={() => handleCheckboxChange(perm.group, 'read')}
                                                    />
                                                </td>
                                                <td>
                                                    <input
                                                        type="checkbox"
                                                        checked={permissions[perm.group]?.update || false}
                                                        onChange={() => handleCheckboxChange(perm.group, 'update')}
                                                    />
                                                </td>
                                                <td>
                                                    <input
                                                        type="checkbox"
                                                        checked={permissions[perm.group]?.delete || false}
                                                        onChange={() => handleCheckboxChange(perm.group, 'delete')}
                                                    />
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </Table>
                            </div>
                        </div>
                    ) : (
                        <p style={{paddingLeft:'15px', paddingTop:'10px'}}>No permissions available for this role.</p>
                    )}
                </Col>
            </Card>
                {/* Save Button */}
                <div style={{ textAlign: 'right', marginTop: '20px' }}>
                    <Button color="primary" onClick={handleSave}>
                        Save
                    </Button>
                </div>
            {/* Toast Container */}
            <ToastContainer />
        </Fragment>
    );
};

export default RolePermissionUpdate;
