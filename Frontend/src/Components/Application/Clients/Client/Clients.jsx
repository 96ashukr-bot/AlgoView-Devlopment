import React, { Fragment, useState, useEffect } from 'react';
import {
    Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink,
    Input, Button, Form, FormGroup, Label, Row, Dropdown, DropdownToggle, DropdownMenu, DropdownItem
} from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import { FaArrowUp, FaArrowDown, FaEdit, FaTrash } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import Swal from 'sweetalert2';
import { getClients, deleteClient } from '../../../../Services/Authentication';

const Clients = () => {
    const [currentPage, setCurrentPage] = useState(1);
    const [clients, setClients] = useState([]);
    const [itemsPerPage] = useState(10);
    const [searchQuery, setSearchQuery] = useState('');
    const [dropdownOpen, setDropdownOpen] = useState(false);
    const [formData, setFormData] = useState({
        clientType: '',
        brokerType: '',
        tradingType: '',
    });

    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const navigate = useNavigate();

    const toggleDropdown = () => setDropdownOpen((prevState) => !prevState);

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

    useEffect(() => {
        fetchClients();
    }, []);

    const fetchClients = async () => {
        try {
            const response = await getClients();
            setClients(response.results);
        } catch (error) {
            console.error('Error fetching clients:', error);
        }
    };

    const filteredClients = clients.filter((client) =>
        Object.values(client).some((value) =>
            value.toString().toLowerCase().includes(searchQuery.toLowerCase())
        )
    );

    const indexOfLastClient = currentPage * itemsPerPage;
    const indexOfFirstClient = indexOfLastClient - itemsPerPage;
    const currentClients = filteredClients.slice(indexOfFirstClient, indexOfLastClient);
    const totalPages = Math.ceil(filteredClients.length / itemsPerPage);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({ ...formData, [name]: value });
    };

    const handleEdit = (client) => {
        console.log('Edit client:', client);
        navigate(`/dashboard/clients/editclient/:id`);
    };

    const handleDelete = (client) => {
        Swal.fire({
            title: 'Are you sure you want to delete?',
            text: `You are about to delete the client "${client.firstName}".`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Yes',
            cancelButtonText: 'Cancel',
        }).then(async (result) => {
            if (result.isConfirmed) {
                try {
                    await deleteClient(client.id);
                    Swal.fire('Deleted!', 'The client has been deleted successfully.', 'success');
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

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <div className="d-flex justify-content-between align-items-center">
                            <div>
                                <H3>Clients</H3>
                                <span>Below is the list of clients along with their details.</span>
                            </div>
                            <div className="d-flex">
                                <Input
                                    type="text"
                                    placeholder="Search..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    style={{ width: '200px', marginRight: '10px' }}
                                />
                                <Button className="search-btn-clr">Search</Button>
                                <Dropdown isOpen={dropdownOpen} toggle={toggleDropdown} className="ms-3">
                                    <DropdownMenu end>
                                        <DropdownItem onClick={() => navigate('/dashboard/addclient/:layout')}>
                                            Add Client
                                        </DropdownItem>
                                    </DropdownMenu>
                                </Dropdown>
                            </div>
                        </div>

                        <Form className="mt-3">
                            <Row form>
                                <Col md={4}>
                                    <FormGroup>
                                        <Label for="clientType">Client Type</Label>
                                        <Input
                                            type="select"
                                            name="clientType"
                                            id="clientType"
                                            value={formData.clientType}
                                            onChange={handleInputChange}
                                        >
                                            <option value="">All</option>
                                            <option value="Individual">Individual</option>
                                            <option value="Corporate">Corporate</option>
                                        </Input>
                                    </FormGroup>
                                </Col>
                                <Col md={4}>
                                    <FormGroup>
                                        <Label for="brokerType">Broker Type</Label>
                                        <Input
                                            type="select"
                                            name="brokerType"
                                            id="brokerType"
                                            value={formData.brokerType}
                                            onChange={handleInputChange}
                                        >
                                            <option value="">All</option>
                                            <option value="Broker A">Broker A</option>
                                            <option value="Broker B">Broker B</option>
                                        </Input>
                                    </FormGroup>
                                </Col>
                                <Col md={4} className="d-flex align-items-end">
                                    <FormGroup className="flex-grow-1 me-2">
                                        <Label for="tradingType">Trading Type</Label>
                                        <Input
                                            type="select"
                                            name="tradingType"
                                            id="tradingType"
                                            value={formData.tradingType}
                                            onChange={handleInputChange}
                                        >
                                            <option value="">All</option>
                                            <option value="Intraday">Intraday</option>
                                            <option value="Delivery">Delivery</option>
                                        </Input>
                                    </FormGroup>
                                    <Button
                                        style={{ marginBottom: '18px' }}
                                        onClick={() => navigate('/dashboard/addclient/:layout')}
                                        className="ms-2 search-btn-clr"
                                    >
                                        Add Client
                                    </Button>
                                </Col>
                            </Row>
                        </Form>
                    </CardHeader>

                    <div className="card-block row">
                        <Col sm="12" lg="12" xl="12">
                            <div className="table-responsive-sm">
                                <Table>
                                <thead>
                                        <tr>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>Sr. No.</th>
                                            <th onClick={() => handleSort('name')} style={{ backgroundColor: '#283F7B', color: 'white', cursor: 'pointer', }}>Client Name <FaArrowUp className="arrow-icon" /> <FaArrowDown  className="arrow-icon"/></th>
                                            <th onClick={() => handleSort('email')} style={{ backgroundColor: '#283F7B', color: 'white', cursor: 'pointer', }}>Email <FaArrowUp className="arrow-icon" /> <FaArrowDown  className="arrow-icon"/></th>
                                            <th onClick={() => handleSort('name')} style={{ backgroundColor: '#283F7B', color: 'white', cursor: 'pointer', }}>Full Name <FaArrowUp className="arrow-icon" /> <FaArrowDown  className="arrow-icon"/></th>
                                            {/* <th onClick={() => handleSort('client_key')} style={{ backgroundColor: '#283F7B', color: 'white', cursor: 'pointer', }}>Client Key <FaArrowUp className="arrow-icon" /> <FaArrowDown  className="arrow-icon"/></th> */}
                                            <th onClick={() => handleSort('phone')} style={{ backgroundColor: '#283F7B', color: 'white', cursor: 'pointer', }}>Phone No. <FaArrowUp className="arrow-icon" /> <FaArrowDown  className="arrow-icon"/></th>
                                            <th onClick={() => handleSort('broker')} style={{ backgroundColor: '#283F7B', color: 'white', cursor: 'pointer', }}>Broker <FaArrowUp className="arrow-icon" /> <FaArrowDown  className="arrow-icon"/></th>
                                            <th onClick={() => handleSort('month')} style={{ backgroundColor: '#283F7B', color: 'white', cursor: 'pointer', }}>Month <FaArrowUp className="arrow-icon" /> <FaArrowDown  className="arrow-icon"/></th>
                                            <th onClick={() => handleSort('status')} style={{ backgroundColor: '#283F7B', color: 'white', cursor: 'pointer', }}>Status <FaArrowUp className="arrow-icon" /> <FaArrowDown  className="arrow-icon"/></th>
                                            <th style={{backgroundColor:'#283F7B',color:'white'}}>Dashboard</th>
                                            <th style={{ backgroundColor: '#283F7B', color: 'white' }}>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {currentClients.map((client, index) => (
                                            <tr key={index}>
                                                <td>{indexOfFirstClient + index + 1}</td>
                                                <td>{client.firstName}</td>
                                                <td>{client.email}</td>
                                                <td>{client.fullName}</td>
                                                {/* <td>{client.client_key}</td> */}
                                                <td>{client.phoneNumber}</td>
                                                <td>{client.Broker?.broker_name || 'N/A'}</td>
                                                <td>{client.to_month}</td>
                                                <td>{client.client_status ? 'Active' : 'Inactive'}</td>
                                                <td>Dashboard</td>
                                                <td>
                                                    <FaEdit onClick={() => handleEdit(client)} style={{ cursor: 'pointer', marginRight: '10px', color: 'blue' }} />
                                                    <FaTrash onClick={() => handleDelete(client)} style={{ cursor: 'pointer', color: 'red' }}/>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </Table>
                            </div>
                            <div className="d-flex justify-content-end">
                                <Pagination>
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
                            </div>
                        </Col>
                    </div>
                </Card>
            </Col>
        </Fragment>
    );
};

export default Clients;
