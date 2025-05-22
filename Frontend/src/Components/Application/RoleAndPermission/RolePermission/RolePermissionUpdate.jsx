import React, { Fragment, useEffect, useState, useRef } from 'react';
import { Col, Card, Table, CardHeader, Button, Input } from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import { fetchRolePermissions, updateRolePermissions, fetchRolesList } from '../../../../Services/Authentication';
import { useParams, useNavigate } from 'react-router-dom';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './RolePermission.css';

const RolePermissionUpdate = () => {
    const { layout } = useParams();
    const navigate = useNavigate();
    const [allPermissions, setAllPermissions] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [rolesList, setRolesList] = useState([]);
    const [filteredRoles, setFilteredRoles] = useState([]);
    const [selectedRole, setSelectedRole] = useState(null);
    const [showDropdown, setShowDropdown] = useState(false); 
    const dropdownRef = useRef(null); 
    useEffect(() => {
        const getPermissions = async () => {
            try {
                const data = await fetchRolePermissions();
                setAllPermissions(data);
            } catch (error) {
                toast.error("Failed to fetch permissions. Please check your credentials.");
            }
        };
        getPermissions();
    }, []);

    useEffect(() => {
        const getRoles = async () => {
            try {
                const data = await fetchRolesList();
                setRolesList(data);
                setFilteredRoles(data);
            } catch (error) {
                toast.error("Failed to fetch roles list.");
            }
        };
        getRoles();
    }, []);

    const handleSearchChange = (e) => {
        const searchValue = e.target.value;
        setSearchTerm(searchValue);
        if (searchValue) {
            setFilteredRoles(
                rolesList.filter(role =>
                    role.name.toLowerCase().includes(searchValue.toLowerCase())
                )
            );
        } else {
            setFilteredRoles(rolesList);
        }
        setShowDropdown(true); 
    };

    const handleRoleSelect = (role) => {
        setSelectedRole(role); 
        setSearchTerm(role.name); 
        setShowDropdown(false);
    };

    const handleCheckboxChange = (roleId, group, perm) => {
        setAllPermissions(prevRoles => {
            return prevRoles.map(role => {
                if (role.role.id === roleId) {
                    const updatedPermissions = { ...role };
                    const groupPermissions = updatedPermissions.permissions.find(p => p.group.toLowerCase() === group.toLowerCase());
    
                    if (groupPermissions) {
                        const existingPerms = groupPermissions.permission.split(', ');
    
                        if (existingPerms.includes(perm)) {
                            updatedPermissions.permissions = updatedPermissions.permissions.map(p => {
                                if (p.group.toLowerCase() === group.toLowerCase()) {
                                    return {
                                        ...p,
                                        permission: existingPerms.filter(p => p !== perm).join(', '),
                                    };
                                }
                                return p;
                            });
                        } else {
                            updatedPermissions.permissions = updatedPermissions.permissions.map(p => {
                                if (p.group.toLowerCase() === group.toLowerCase()) {
                                    return {
                                        ...p,
                                        permission: [...existingPerms, perm].join(', '),
                                    };
                                }
                                return p;
                            });
                        }
                    } else {
                        updatedPermissions.permissions.push({
                            group,
                            permission: perm,
                        });
                    }
    
                    return updatedPermissions;
                }
                return role;
            });
        });
    };
    

    const handleSave = async () => {
        try {
            const updates = allPermissions.map(role => {
                const roleId = role.role.id;
                const permissionsObject = {};

                role.permissions.forEach(permission => {
                    permissionsObject[permission.group] = {
                        ...(permissionsObject[permission.group] || {}),
                        [permission.permission]: true,
                    };
                });

                return updateRolePermissions(roleId, permissionsObject);
            });

            await Promise.all(updates);
            toast.success("Permissions updated successfully for all roles!");
        } catch (error) {
            toast.error("Failed to update permissions. Please try again.");
        }
    };

    const handleCancel = () => {
        navigate(`/dashboard/rolepermmision/${layout}`);
    };

    const getDefaultGroups = () => {
        const groups = new Set();
        allPermissions.forEach(role => {
            role.permissions.forEach(permission => {
                groups.add(permission.group.toLowerCase());
            });
        });
        return Array.from(groups).map(group => ({
            group: group.charAt(0).toUpperCase() + group.slice(1),
            permissions: [
                ['create', 'read'],
                ['update', 'delete']
            ]
        }));
    };

    const defaultGroups = getDefaultGroups();

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setShowDropdown(false); 
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    return (
        <Fragment>
            <Card>
                <CardHeader>
                    <H3>Role & Permission</H3>
                    <span>Below is the list of roles & permissions along with their details.</span>
                </CardHeader>

                {/* Search Input with Dropdown */}
                <CardHeader className='input-design' ref={dropdownRef}>
                    <Col md={6} className=" mt-3" style={{ position: 'relative' }}>
                        <Input
                            style={{ width: '50%', marginLeft: '25px' }}
                            type="text"
                            placeholder="Search Roles..."
                            value={searchTerm}
                            onChange={handleSearchChange}
                            onClick={() => setShowDropdown(true)} 
                        />
                        {/* Role List Dropdown */}
                        {showDropdown && (
                            <div className="dropdown-list" style={{
                                position: 'absolute', 
                                top: '100%', 
                                left: '25px', 
                                width: '50%', 
                                maxHeight: '200px', 
                                overflowY: 'auto', 
                                backgroundColor: 'white', 
                                border: '1px solid #ddd', 
                                zIndex: 10
                            }}>
                                {filteredRoles.length > 0 ? (
                                    filteredRoles.map(role => (
                                        <div
                                            key={role.id}
                                            className="dropdown-item"
                                            onClick={() => handleRoleSelect(role)}
                                            style={{
                                                padding: '10px',
                                                cursor: 'pointer',
                                                borderBottom: '1px solid #ddd'
                                            }}
                                        >
                                            {role.name}
                                        </div>
                                    ))
                                ) : (
                                    <div style={{ padding: '10px' }}>No roles found.</div>
                                )}
                            </div>
                        )}
                    </Col>
                </CardHeader>

                <Col>
                    {selectedRole ? (
                        <div>
                            <CardHeader>
                                <h5>{selectedRole.name.charAt(0).toUpperCase() + selectedRole.name.slice(1)}</h5>
                                <span>Below is the list of roles & permissions for {selectedRole.name.charAt(0).toUpperCase() + selectedRole.name.slice(1)}.</span>
                            </CardHeader>
                            <div className="table-responsive" style={{ overflow: 'visible' }}>
                                <Table className="table-responsive-sm" style={{ width: '100%' }}>
                                    <thead>
                                        <tr>
                                            <th style={{ backgroundColor: '#f3f3f3' }}>Name</th>
                                            <th style={{ backgroundColor: '#f3f3f3' }}>Role</th>
                                            <th style={{ backgroundColor: '#f3f3f3' }}>Permission</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {defaultGroups.map((group, index) => (
                                            <tr key={`${group.group}-${index}`}>
                                                <td>{group.group}</td>
                                                <td>{selectedRole.name}</td>
                                                <td>
                                                    {group.permissions.map((permPair, permIndex) => (
                                                        <div key={`${group.group}-${permIndex}`}>
                                                            {permPair.map(perm => (
                                                                <label key={perm} style={{ width: '30%', paddingBottom: '20px', display: 'inline-flex' }}>
                                                                    {perm}
                                                                    <input
                                                                        type="checkbox"
                                                                        style={{
                                                                            marginLeft: '20px',
                                                                            transform: 'scale(1.3)',
                                                                            transformOrigin: 'center',
                                                                        }}
                                                                        checked={allPermissions.some(p => p.role.id === selectedRole.id && p.permissions.some(g => g.group.toLowerCase() === group.group.toLowerCase() && g.permission.includes(perm)))}
                                                                        onChange={() => handleCheckboxChange(selectedRole.id, group.group, perm)}
                                                                    />
                                                                </label>
                                                            ))}
                                                        </div>
                                                    ))}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </Table>
                            </div>
                        </div>
                    ) : (
                        <div style={{ marginLeft: '25px' }}>Please select a role to view permissions.</div>
                    )}
                </Col>

                <div className="card-footer">
                    <Button className='search-btn-clr' onClick={handleSave}>Save</Button>
                    <Button color="danger" style={{ marginLeft: '10px' }} onClick={handleCancel}>Cancel</Button>
                </div>
            </Card>

            <ToastContainer />
        </Fragment>
    );
};

export default RolePermissionUpdate;
