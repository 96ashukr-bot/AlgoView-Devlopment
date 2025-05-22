import React, { Fragment, useState, useEffect } from 'react';
import {
    Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink,
    Input, Button, Row, FormGroup, Label
} from 'reactstrap';
import { FaTrash } from 'react-icons/fa';
import './ServiceManagement.css';
import Swal from 'sweetalert2';
import { useNavigate, useParams } from 'react-router-dom';
import { getSegments, getGroupServiceById, updateGroupService, getServicesList, getStrategies } from '../../../../Services/Authentication';

const EditGroupService = () => {
    const [services, setServices] = useState([]);
    const [segments, setSegments] = useState([]);
    const [servicesList, setServicesList] = useState([]);
    const [groupName, setGroupName] = useState('');
    const [strategies, setStrategies] = useState([]);
    const [selectedStrategies, setSelectedStrategies] = useState([]);
    const [segment, setSegment] = useState('');
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage] = useState(10);
    const [searchQuery, setSearchQuery] = useState('');
    const navigate = useNavigate();
    const { serviceId } = useParams();

    const productTypes = ["CNC", "MIS", "NRML"];

    useEffect(() => {
        fetchData();
        fetchStrategies();
    }, [serviceId]);

    const fetchData = async () => {
        try {
            const groupServiceResponse = await getGroupServiceById(serviceId);
            const segmentsResponse = await getSegments();
            const servicesListResponse = await getServicesList();
            setServices(groupServiceResponse.json_data || []);
            setSegments(segmentsResponse.results || []);
            setGroupName(groupServiceResponse.group_name || '');
            setSegment(groupServiceResponse.segment?.name || '');
            setServicesList(servicesListResponse || []);

            if (groupServiceResponse.Strategy && Array.isArray(groupServiceResponse.Strategy)) {
                const selectedStrategyIds = groupServiceResponse.Strategy.map(strategy => strategy.id);
                setSelectedStrategies(selectedStrategyIds);
            }

            fetchStrategies();

        } catch (error) {
            console.error('Error fetching data:', error);
        }
    };

    const fetchStrategies = async () => {
        try {
            const groupServiceResponse = await getStrategies();
            console.log('Response:', groupServiceResponse);

            const strategies = groupServiceResponse?.results;

            if (Array.isArray(strategies)) {
                console.log('Fetched strategies:', strategies);
                setStrategies(strategies);
            } else {
                console.error('Fetched strategies are not an array:', strategies);
                console.error('Invalid strategies data.');
                setStrategies([]);
            }
        } catch (error) {
            console.error('Error fetching strategies:', error);
            console.error('Failed to load strategies.');
            setStrategies([]);
        }
    };

    const handleDelete = (index) => {
        const updatedServices = services.filter((_, i) => i !== index);
        setServices(updatedServices);
    };

    const handleAddRow = () => {
        const selectedSegment = segments.find((seg) => seg.name === segment);

        setServices([
            ...services,
            { segment: selectedSegment?.id || '', ServiceName: '', LotSize: '', Qty: '', ProductType: '' }
        ]);
    };

    const handleSegmentChange = (event) => {
        const segmentId = event.target.value;
        setSegment(segmentId);
    };

    const handleQtyChange = (index, value) => {
        const updatedServices = [...services];
        updatedServices[index].Qty = value;
        setServices(updatedServices);
    };

    const handleLotSizeChange = (index, value) => {
        const updatedServices = [...services];
        updatedServices[index].LotSize = value;
        setServices(updatedServices);
    };

    const handleProductTypeChange = (index, value) => {
        const updatedServices = [...services];
        updatedServices[index].ProductType = value;
        setServices(updatedServices);
    };

    const handleServiceNameChange = (index, serviceId) => {
        const updatedServices = [...services];
        const selectedService = servicesList.find((service) => service.id === parseInt(serviceId));
        updatedServices[index].ServiceName = selectedService?.service_name || '';
        setServices(updatedServices);
    };


    const handleSave = async () => {
        try {
            // Find the selected segment's ID based on the name
            const selectedSegment = segments.find((seg) => seg.name === segment);

            const payload = {
                group_name: groupName,
                segment: selectedSegment?.id || '',
                Strategy: selectedStrategies,
                json_data: services,
            };

            await updateGroupService(serviceId, payload);
            Swal.fire({
                title: `Group Service Updated successfully`,
                icon: 'success',
                showCancelButton: true,
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33',
                confirmButtonText: 'OK',
            });
            navigate('/service-manage/group-services-list');
        } catch (error) {
            console.error('Error updating group service:', error);
            Swal.fire('Failed to update group service.');
        }
    };

    const handleCheckboxChange = (strategy) => {
        if (!strategy) {
            console.error('Strategy is undefined');
            return; // Exit the function if strategy is undefined
        }

        // Check if the strategy is already selected
        if (selectedStrategies.includes(strategy.id)) {
            // Remove it if already selected
            setSelectedStrategies(selectedStrategies.filter(id => id !== strategy.id));
        } else {
            // Add it to the selected strategies
            setSelectedStrategies([...selectedStrategies, strategy.id]);
        }
    };

    const handleCancel = () => {
        navigate('/service-manage/group-services-list');
    };

    const filteredServices = services.filter((item) =>
        item.ServiceName?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const indexOfLastService = currentPage * itemsPerPage;
    const indexOfFirstService = indexOfLastService - itemsPerPage;
    const currentServices = filteredServices.slice(indexOfFirstService, indexOfLastService);
    const totalPages = Math.ceil(filteredServices.length / itemsPerPage);

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <div className="d-flex justify-content-between align-items-center custom-responsive-style">
                            <div>
                                <h3>Edit Group Service</h3>
                                <span>Manage services by group and segment.</span>
                            </div>
                            <div className='custom-responsive-style-search' style={{ display: 'flex' }}>
                                <Input
                                    type="text"
                                    placeholder="Search..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    style={{ width: '200px', marginRight: '10px' }}
                                />
                                <Button className="search-btn-clr">Search</Button>
                            </div>
                        </div>
                    </CardHeader>
                    <div className="card-block row" style={{ padding: '20px' }}>
                        <Row>
                            <Col sm="4">
                                <FormGroup>
                                    <Label for="groupName">Group Name
                                        <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                                    </Label>
                                    <Input
                                        type="text"
                                        id="groupName"
                                        value={groupName}
                                        className='custom-input-style'
                                        onChange={(e) => setGroupName(e.target.value)}
                                        placeholder="Enter Group Name"
                                    />
                                </FormGroup>

                                <FormGroup>
                                    <Label for="segment">Segment
                                        <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                                    </Label>
                                    <Input
                                        type="select"
                                        id="segment"
                                        value={segment}
                                        className='custom-input-style'
                                        onChange={handleSegmentChange}
                                    >
                                        <option value="">Select Segment</option>
                                        {segments.map((seg) => (
                                            <option key={seg.id} value={seg.id}>
                                                {seg.name}
                                            </option>
                                        ))}
                                    </Input>
                                </FormGroup>
                                <FormGroup>
                                    <Label for="strategy"> Strategy
                                        <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                                    </Label>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px' }}>
                                        {strategies.map((strategy) => (
                                            <label key={strategy.id} style={{ display: 'flex', alignItems: 'center' }}>
                                                <input
                                                    type="checkbox"
                                                    style={{
                                                        marginRight: '5px',
                                                        transform: 'scale(1.3)',
                                                        transformOrigin: 'center',
                                                    }}
                                                    checked={selectedStrategies.includes(strategy.id)}
                                                    onChange={() => handleCheckboxChange(strategy)}
                                                />
                                                <span>{strategy.name}</span>
                                            </label>
                                        ))}
                                    </div>
                                </FormGroup>
                            </Col>

                            <Col sm="8">
                                <div className="table-responsive-sm">
                                    <Table bordered className='custom-table-design' responsive>
                                        <thead>
                                            <tr>
                                                <th style={{ backgroundColor: '#283F7B', color: 'white' }}>S.No</th>
                                                <th style={{ backgroundColor: '#283F7B', color: 'white' }}>Segment</th>
                                                <th style={{ backgroundColor: '#283F7B', color: 'white' }}>Service Name</th>
                                                <th style={{ backgroundColor: '#283F7B', color: 'white' }}>Lot Size</th>
                                                <th style={{ backgroundColor: '#283F7B', color: 'white' }}>Qty</th>
                                                <th style={{ backgroundColor: '#283F7B', color: 'white' }}>Product Type</th>
                                                <th style={{ backgroundColor: '#283F7B', color: 'white' }}>Action</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {currentServices.map((service, index) => (
                                                <tr key={index}>
                                                    <td>{indexOfFirstService + index + 1}</td>
                                                    <td>
                                                        <Input
                                                            type="select"
                                                            id="segment"
                                                            value={segment}
                                                            className='custom-input-style'
                                                            onChange={(e) => setSegment(e.target.value)}
                                                        >
                                                            <option value="">Select Segment</option>
                                                            {segments.map((seg) => (
                                                                <option key={seg.id} value={seg.name}>
                                                                    {seg.name}
                                                                </option>
                                                            ))}
                                                        </Input>
                                                    </td>
                                                    <td>
                                                        <Input
                                                            type="select"
                                                            value={servicesList.find((s) => s.service_name === service.ServiceName)?.id || ''}
                                                            onChange={(e) => handleServiceNameChange(index, e.target.value)}
                                                        >
                                                            <option value="">Select Service Name</option>
                                                            {servicesList.map((serviceOption) => (
                                                                <option key={serviceOption.id} value={serviceOption.id}>
                                                                    {serviceOption.service_name}
                                                                </option>
                                                            ))}
                                                        </Input>
                                                    </td>
                                                    <td>
                                                        <Input
                                                            style={{ width: '100px' }}
                                                            type="text"
                                                            value={service.LotSize || ''}
                                                            onChange={(e) => handleLotSizeChange(index, e.target.value)}
                                                        />
                                                    </td>

                                                    <td>
                                                        <Input
                                                            style={{ width: '100px' }}
                                                            type="number"
                                                            value={service.Qty || ''}
                                                            onChange={(e) => handleQtyChange(index, e.target.value)}
                                                        />
                                                    </td>
                                                    <td>
                                                        <Input
                                                            type="select"
                                                            value={service.ProductType || ''}
                                                            onChange={(e) => handleProductTypeChange(index, e.target.value)}
                                                        >
                                                            <option value="">Select Type</option>
                                                            {productTypes.map((type, i) => (
                                                                <option key={i} value={type}>
                                                                    {type}
                                                                </option>
                                                            ))}
                                                        </Input>
                                                    </td>

                                                    <td>
                                                        <FaTrash
                                                            color="red"
                                                            style={{ cursor: 'pointer' }}
                                                            onClick={() => handleDelete(index)}
                                                        />
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </Table>
                                    <Button onClick={handleAddRow} className="mt-2 search-btn-clr">
                                        Add More
                                    </Button>
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

                                <Row className="mt-4">
                                    <div className="d-flex justify-content-end mt-3">
                                        {/* <Col md="12" className="text-right"> */}
                                        <Button color="primary" className="mt-4 search-btn-clr" onClick={handleSave}>
                                            Update
                                        </Button>
                                        <Button
                                            color="danger"
                                            className="mt-4 ml-2"
                                            style={{ marginLeft: '10px' }}
                                            onClick={handleCancel}
                                        >
                                            Cancel
                                        </Button>
                                        {/* </Col> */}
                                    </div>
                                </Row>
                            </Col>
                        </Row>
                    </div>
                </Card>
            </Col>
        </Fragment>
    );
};

export default EditGroupService;
