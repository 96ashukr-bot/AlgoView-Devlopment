import React, { Fragment, useState, useEffect } from 'react';
import {
    Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink,
    Input, Button, Form, FormGroup, Label, Row, Dropdown, DropdownToggle, DropdownMenu, DropdownItem, Badge
} from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import { FaArrowUp, FaArrowDown, FaEdit, FaTrash, FaEye, FaPencilAlt, FaTrashAlt } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import { RotatingLines } from 'react-loader-spinner';
import Swal from 'sweetalert2';
import { getClients, deleteClient, fetchUserProfile, updateClientStatus, getLicence, getClientsFilter, SearchAllClients, getTradeCounts } from '../../../../Services/Authentication';
import './Clients.css';

const AllClients = () => {
    const [currentPage, setCurrentPage] = useState(1);
    const [clients, setClients] = useState([]);
    const [itemsPerPage, setItemsPerPage] = useState(10);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [totalPages, setTotalPages] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [licenses, setLicenses] = useState([]);
    const [selectedTradeType, setSelectedTradeType] = useState('');
    const [selectedClientType, setSelectedClientType] = useState('');
    const [dropdownOpen, setDropdownOpen] = useState(false);
    const [userRole, setUserRole] = useState("");
    const [isMobile, setIsMobile] = useState(false);
    const [pageBatch, setPageBatch] = useState(0);
    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const [totalClients, setTotalClients] = useState(0);
    const [activeClients, setActiveClients] = useState(0);
    const [inactiveClients, setInactiveClients] = useState(0);

    const navigate = useNavigate();

    const toggleDropdown = () => setDropdownOpen((prevState) => !prevState);

    useEffect(() => {
        if (searchQuery) {
            handleSearch();
        } else {
            fetchClients();
        }

        const handleResize = () => {
            setIsMobile(window.innerWidth <= 768);
        };

        handleResize();
        window.addEventListener('resize', handleResize);

        return () => window.removeEventListener('resize', handleResize);

    }, [currentPage, itemsPerPage, searchQuery]);

    useEffect(() => {
        fetchClientTradeCount();
        fetchUserRole();
        fetchLicenses();
    }, []);

    const pagesPerBatch = isMobile ? 2 : 4;

    const fetchClients = async () => {
        try {
            setLoading(true);
            const response = await getClients(currentPage, itemsPerPage);

            if (response.results && response.results.length > 0) {
                setClients(response.results); // Directly store the paginated data.
                setTotalPages(Math.ceil(response.count / itemsPerPage));
                setTotalClients(response.count);
            } else {
                setClients([]); // Handle empty pages.
            }
        } catch (err) {
            console.error("Error fetching data:", err);
            setError("Failed to load data.");
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = async () => {
        try {
            setLoading(true);
            const response = await SearchAllClients(searchQuery);
            if (response?.results?.length > 0) {
                setClients(response.results);
            } else {
                setClients([]);
            }
        } catch (error) {
            console.error('Error during search:', error);
            setError("Search failed.");
        } finally {
            setLoading(false);
        }
    };

    const fetchUserRole = async () => {
        try {
            const data = await fetchUserProfile();
            if (data?.role?.name) {
                setUserRole(data.role.name);
            }
        } catch (error) {
            console.error('Error fetching user profile:', error);
        }
    };

    const fetchLicenses = async () => {
        try {
            const response = await getLicence();
            console.log('License Response:', response);
            if (response && Array.isArray(response.results)) {
                setLicenses(response.results);
            } else {
                console.error('Fetched licenses are not an array:', response);
                setLicenses([]);
            }
        }
        catch (error) {
            console.error('Error fetching licenses:', error);
            setLicenses([]);
        }
    };

    const fetchFilteredClients = async (clientType, tradeType) => {
        try {
            const response = await getClientsFilter(clientType, tradeType, itemsPerPage);
            setClients(response.results || []);
        } catch (error) {
            console.error('Error fetching filtered clients:', error);
        }
    };

    const fetchClientTradeCount = async () => {
        try {
            const response = await getTradeCounts();
            if (response) {
                setActiveClients(response.active_clients || 0);
                setInactiveClients(response.inactive_clients || 0);
            }
        } catch (error) {
            console.error('Error fetching client trade counts:', error);
        }
    };

    const handleToggleStatus = async (clientId, currentState) => {
        const payload = { client_status: !currentState };
        try {
            const response = await updateClientStatus(clientId, payload);
            Swal.fire(
                'Success!',
                `Client status updated to ${response.client_status ? '"Active"' : '"Inactive"'}.`,
                'success'
            );
            // Update the client list in state
            const updatedClients = clients.map(client =>
                client.id === clientId ? { ...client, client_status: response.client_status } : client
            );
            setClients(updatedClients);
        } catch (error) {
            console.error('Error updating client status:', error);
            Swal.fire('Error!', 'Could not update client status. Please try again.', 'error');
        }
    };

    const handleEdit = (client) => {
        console.log('Edit client:', client);
        navigate(`/client/all-clients-list/edit-client/${client.id}`);
    };

    const handleViewClient = (client) => {
        console.log('View client Details:', client);
        navigate(`/client/all-clients-list/client-details/${client.id}`, { state: { clientId: client.id } });
    };

    const handleDelete = (client) => {
        Swal.fire({
            title: 'Are you sure want to delete ?',
            text: `You are about to delete the client "${client.userName}".`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Yes',
            cancelButtonText: 'Cancel'
        }).then(async (result) => {
            if (result.isConfirmed) {
                try {
                    await deleteClient(client.id);
                    Swal.fire(
                        'Deleted!',
                        'The client has been deleted successfully.',
                        'success'
                    );
                    fetchClients();
                } catch (error) {
                    console.error('Error deleting client:', error);
                    Swal.fire(
                        'Error!',
                        'There was an issue deleting the client. Please try again later.',
                        'error'
                    );
                }
            }
        });
    };

    const handleClientTypeChange = (e) => {
        const value = e.target.value;
        setSelectedClientType(value);
        fetchFilteredClients(value, selectedTradeType);
    };

    const handleTradeTypeChange = (e) => {
        const value = e.target.value;
        setSelectedTradeType(value);
        fetchFilteredClients(selectedClientType, value);
    };

    const handleReset = () => {
        setSelectedClientType('');
        setSelectedTradeType('');
        fetchClients();
    };

    const filteredClients = clients.filter(client => {
        const matchesSearchQuery = Object.values(client).some(value =>
            value != null && value.toString().toLowerCase().includes(searchQuery.toLowerCase())
        );
        const matchesClientType = selectedClientType === '' || (client.license && client.license.name === selectedClientType);
        return matchesSearchQuery && matchesClientType;
    });

    const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });

        const sortedClients = [...clients].sort((a, b) => {
            if (a[key] < b[key]) return direction === 'asc' ? -1 : 1;
            if (a[key] > b[key]) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        setClients(sortedClients);
    };

    const indexOfLastClient = currentPage * itemsPerPage;
    const indexOfFirstClient = indexOfLastClient - itemsPerPage;

    let currentClients = filteredClients;

    if (currentPage === 1 && filteredClients.length > itemsPerPage) {
        const extraItem = filteredClients[filteredClients.length - 1];
        currentClients = [extraItem, ...currentClients.slice(0, itemsPerPage - 1)];
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

    return (
        <Fragment>
            <Col sm="12">
                <Card style={{ marginTop: '80px' }}>
                    <CardHeader>
                        <div className="d-flex justify-content-between align-items-center custom-responsive-style">
                            <div>
                                <H3>All Clients</H3>
                            </div>
                            <div>
                                <button className="btn btn-primary search-btn-clr custom-responsive-style-btn" onClick={() => navigate('/client/addclient')} style={{ marginRight: '20px' }}>
                                    Add New Client
                                </button>
                                <Input
                                    type="text"
                                    placeholder="Search..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter') {
                                            handleSearch();
                                        }
                                    }}
                                    style={{ width: '200px', marginRight: '10px', display: 'inline-block' }}
                                />
                                <Button className='search-btn-clr' onClick={handleSearch}>Search</Button>
                            </div>
                        </div>

                        <Form className="mt-3">
                            <Row form>
                                <Col md={3}>
                                    <FormGroup>
                                        <Label for="clientType">Client Type</Label>
                                        <Input
                                            type="select"
                                            id="clientType"
                                            value={selectedClientType}
                                            onChange={handleClientTypeChange}
                                        >
                                            <option value="">All</option>
                                            {licenses.map((license, index) => (
                                                <option key={index} value={license.name}>{license.name}</option>
                                            ))}
                                        </Input>
                                    </FormGroup>
                                </Col>
                                <Col md={3}>
                                    <FormGroup>
                                        <Label for="tradeType">Trading Status</Label>
                                        <Input
                                            type="select"
                                            id="tradeType"
                                            value={selectedTradeType}
                                            onChange={handleTradeTypeChange}
                                        >
                                            <option value="">All</option>
                                            <option value="ON">ON</option>
                                            <option value="OFF">OFF</option>
                                        </Input>
                                    </FormGroup>
                                </Col>
                                <Col md={2} className="mt-4">
                                    <Button className='search-btn-clr' onClick={handleReset}>Reset</Button>
                                </Col>
                            </Row>
                        </Form>

                        <Form className="mt-4">
                            <Row className="d-flex justify-content-between">
                                <Col md="4">
                                    <FormGroup style={{ backgroundColor: "yellow", padding: "10px", borderRadius: "5px" }}>
                                        <h5 className='text-center'>
                                            Total Clients Count: <span style={{ fontWeight: "bold" }}>{totalClients}</span> Clients
                                        </h5>
                                    </FormGroup>
                                </Col>
                                <Col md="4">
                                    <FormGroup style={{ backgroundColor: "green", color: "white", padding: "10px", borderRadius: "5px" }}>
                                        <h5 className='text-center'>
                                            Active Trade Clients: <span style={{ fontWeight: "bold" }}>{activeClients}</span> Clients
                                        </h5>
                                    </FormGroup>
                                </Col>
                                <Col md="4">
                                    <FormGroup style={{ backgroundColor: "red", color: "white", padding: "10px", borderRadius: "5px" }}>
                                        <h5 className='text-center'>
                                            Inactive Trade Clients: <span style={{ fontWeight: "bold" }}>{inactiveClients}</span> Clients
                                        </h5>
                                    </FormGroup>
                                </Col>
                            </Row>
                        </Form>

                    </CardHeader>

                    <div className="card-block row" style={{ height: '100%' }}>
                        <Col sm="12" lg="12" xl="12" style={{ height: '100%' }}>
                            <div className="table-responsive" style={{ height: '100%' }}>
                                <Table>
                                    <thead>
                                        <tr>
                                            <th className='custom-col-design'>Sr. No.</th>
                                            <th onClick={() => handleSort('userName')} className='custom-col-design sortable'>
                                                User Name
                                                <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th onClick={() => handleSort('fullName')} className='custom-col-design sortable'>
                                                Full Name
                                                <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th onClick={() => handleSort('email')} className='custom-col-design sortable'>
                                                Email
                                                <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th onClick={() => handleSort('phoneNumber')} className='custom-col-design sortable'>
                                                Phone No.
                                                <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th onClick={() => handleSort('license')} className='custom-col-design sortable'>
                                                License
                                                <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th onClick={() => handleSort('month')} className='custom-col-design sortable'>
                                                Month
                                                <FaArrowUp className="sort-arrow-left" />
                                                <FaArrowDown className="sort-arrow-right" />
                                            </th>
                                            <th className='custom-col-design'>Status</th>
                                            <th className='custom-col-design'>Trading Status</th>
                                            <th className='custom-col-design'>View Client</th>
                                            {userRole.toLowerCase() !== "sub-admin" && <th style={{ backgroundColor: '#283F7B', color: 'white' }}>Actions</th>}
                                        </tr>
                                    </thead>

                                    <tbody>
                                        {loading ? (
                                            <tr>
                                                <td colSpan="9" style={{ textAlign: 'center', height: '100px' }}>
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
                                        ) : currentClients.map((client, index) => (
                                            <tr key={index}>
                                                <td>{indexOfFirstClient + index + 1}</td>
                                                <td>{client.userName}</td>
                                                <td>{client.fullName}</td>
                                                <td>{client.email}</td>
                                                <td>{client.phoneNumber}</td>
                                                <td>{client.license ? client.license.name : 'N/A'}</td>
                                                <td>{client.to_month ? client.to_month : 'Demo'}</td>
                                                <td>
                                                    <label className="switch">
                                                        <input
                                                            type="checkbox"
                                                            checked={client.client_status}
                                                            onChange={() => handleToggleStatus(client.id, client.client_status)}
                                                        />
                                                        <span className="slider round"></span>
                                                    </label>
                                                </td>
                                                <td>
                                                    <div
                                                        style={{
                                                            width: '12px',
                                                            height: '12px',
                                                            borderRadius: '50%',
                                                            backgroundColor: client.is_enable ? 'green' : 'red',
                                                            marginLeft: '20px'
                                                        }}
                                                    />
                                                </td>

                                                <td>
                                                    <FaEye
                                                        onClick={() => handleViewClient(client)}
                                                        style={{ cursor: 'pointer', marginLeft: '20px', fontSize: '18px' }}
                                                    />
                                                </td>
                                                {userRole.toLowerCase() !== "sub-admin" && (
                                                    <td>
                                                        <FaPencilAlt onClick={() => handleEdit(client)} style={{ cursor: 'pointer', marginRight: '10px', color: '#6d62e7' }} />
                                                        <FaTrashAlt onClick={() => handleDelete(client)} style={{ cursor: 'pointer', color: '#ef3636' }} />
                                                    </td>
                                                )}
                                            </tr>
                                        ))}
                                    </tbody>

                                </Table>
                            </div>

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
                            </div>
                        </Col>
                    </div>
                </Card>
            </Col>
        </Fragment>
    );
};

export default AllClients;
