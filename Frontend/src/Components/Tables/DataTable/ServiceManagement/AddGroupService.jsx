import React, { Fragment, useState, useEffect } from 'react';
import {
    Col, Card, Table, CardHeader, Input, Button, Row, FormGroup, Label
} from 'reactstrap';
import { FaTrash } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import Swal from 'sweetalert2';
import './ServiceManagement.css';
import { getSegmentsList, getServicesList, addGroupService, getStrategies } from '../../../../Services/Authentication';

const AddGroupService = () => {
    const [services, setServices] = useState([
        { segment: '', ServiceName: '', LotSize: '', Qty: '', ProductType: '' }
    ]);
    const [groupName, setGroupName] = useState('');
    const [segments, setSegments] = useState([]);
    const [strategies, setStrategies] = useState([]);
    const [selectedStrategies, setSelectedStrategies] = useState([]);
    const [serviceOptions, setServiceOptions] = useState([]);
    const navigate = useNavigate();

    const ProductType = ['CNC', 'MIS', 'NRML'];

    useEffect(() => {
        fetchData();
        fetchServiceData();
        fetchStrategies();
    }, []);

    const handleInputChange = (index, field, value) => {
        const newServices = [...services];
        newServices[index][field] = value;
        setServices(newServices);
    };

    const handleAddRow = () => {
        setServices([...services, { segment: '', ServiceName: '', LotSize: '', Qty: '', ProductType: '' }]);
    };

    const handleDelete = (index) => {
        const newServices = services.filter((_, i) => i !== index);
        setServices(newServices);
    };

    const handleCancel = () => {
        navigate('/service-manage/group-services-list');
    };

    const fetchData = async () => {
        try {
            const data = await getSegmentsList();
            if (Array.isArray(data)) {
                setSegments(data);
            } else if (data.results) {
                setSegments(data.results);
            } else {
                throw new Error('Unexpected response structure');
            }
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    };

    const fetchServiceData = async () => {
        try {
            const data = await getServicesList();
            if (Array.isArray(data)) {
                setServiceOptions(data);
            } else if (data.results) {
                setServiceOptions(data.results);
            } else {
                throw new Error('Unexpected response structure');
            }
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    };

    const fetchStrategies = async () => {
        try {
            const response = await getStrategies();
            console.log('Response:', response);

            const strategies = response?.results;

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

    const handleCheckboxChange = (strategy) => {
        if (!strategy) return;

        if (selectedStrategies.includes(strategy.id)) {
            setSelectedStrategies(selectedStrategies.filter((id) => id !== strategy.id));
        } else {
            setSelectedStrategies([...selectedStrategies, strategy.id]);
        }
    };

    const handleSave = async () => {
        const payload = {
            group_name: groupName,
            segment: parseInt(services[0].segment),
            Strategy: selectedStrategies,
            json_data: services.map((service, index) => ({
                "S.No": index + 1,
                segment: service.segment,
                ServiceName: service.ServiceName,
                LotSize: service.LotSize,
                Qty: service.Qty,
                ProductType: service.ProductType
            }))
        };

        try {
            const response = await addGroupService(payload);
            console.log('Group Service added successfully:', response);
            Swal.fire({
                title: `Group Service added successfully`,
                icon: 'success',
                showCancelButton: true,
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33',
                confirmButtonText: 'OK',
            });
            navigate('/service-manage/group-services-list');
        } catch (error) {
            console.error('Error adding group service:', error);
            Swal.fire('Failed to add group service.');
        }
    };

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader className="d-flex justify-content-between align-items-center">

                        <div>
                            <h3>Add Group Service</h3>
                            <span>Manage services by group and segment.</span>
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
                                        placeholder="Enter Group Name"
                                        className='custom-input-style'
                                        value={groupName}
                                        onChange={(e) => setGroupName(e.target.value)}
                                    />
                                </FormGroup>

                                <FormGroup>
                                    <Label for="segment">Segment
                                        <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                                    </Label>
                                    <Input
                                        type="select"
                                        id="segment"
                                        className='custom-input-style'
                                        onChange={(e) => handleInputChange(0, 'segment', e.target.value)}
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
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px', marginTop: '10px' }}>
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
                                                <th className='custom-col-design'>S.No</th>
                                                <th className='custom-col-design'>Segment</th>
                                                <th className='custom-col-design'>Service Name</th>
                                                <th className='custom-col-design'>Lot Size</th>
                                                <th className='custom-col-design'>Qty</th>
                                                <th className='custom-col-design'>Product Type</th>
                                                <th className='custom-col-design'>Action</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {services.map((service, index) => (
                                                <tr key={index}>
                                                    <td>{index + 1}</td>
                                                    <td>
                                                        <Input
                                                            type="select"
                                                            value={service.segment}
                                                            onChange={(e) =>
                                                                handleInputChange(index, 'segment', e.target.value)
                                                            }
                                                        >
                                                            <option value="">Select Segment</option>
                                                            {segments.map((seg) => (
                                                                <option key={seg.id} value={seg.id}>
                                                                    {seg.name}
                                                                </option>
                                                            ))}
                                                        </Input>
                                                    </td>
                                                    <td>
                                                        <Input
                                                            type="select"
                                                            value={service.ServiceName}
                                                            onChange={(e) =>
                                                                handleInputChange(index, 'ServiceName', e.target.value)
                                                            }
                                                        >
                                                            <option value="">Select Service</option>
                                                            {serviceOptions.map((svc) => (
                                                                <option key={svc.id} value={svc.service_name}>
                                                                    {svc.service_name}
                                                                </option>
                                                            ))}
                                                        </Input>
                                                    </td>
                                                    <td>
                                                        <Input
                                                            type="number"
                                                            value={service.LotSize}
                                                            onChange={(e) => handleInputChange(index, 'LotSize', e.target.value)}
                                                        />
                                                    </td>
                                                    <td>
                                                        <Input
                                                            type="number"
                                                            value={service.Qty}
                                                            onChange={(e) => handleInputChange(index, 'Qty', e.target.value)}
                                                        />
                                                    </td>
                                                    <td>
                                                        <Input
                                                            type="select"
                                                            value={service.ProductType}
                                                            onChange={(e) => handleInputChange(index, 'ProductType', e.target.value)}
                                                        >
                                                            <option value="">Select Product Type</option>
                                                            {ProductType.map((type) => (
                                                                <option key={type} value={type}>
                                                                    {type}
                                                                </option>
                                                            ))}
                                                        </Input>
                                                    </td>
                                                    <td>
                                                        <FaTrash color="red" style={{ cursor: 'pointer' }} onClick={() => handleDelete(index)} />
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </Table>
                                    <Button onClick={handleAddRow} className="mt-2 search-btn-clr">
                                        Add More
                                    </Button>
                                </div>
                            </Col>
                        </Row>
                        <div className="d-flex justify-content-end mt-3">
                            <Button className='search-btn-clr' onClick={handleSave} style={{ marginRight: '10px' }}>
                                Save
                            </Button>
                            <Button color="danger" onClick={handleCancel}>
                                Cancel
                            </Button>
                        </div>
                    </div>
                </Card>
            </Col>
        </Fragment>
    );
};

export default AddGroupService;
