import React, { useEffect, useState } from 'react';
import { Container, Row, Col, Card, CardBody, Form, FormGroup, Label, Input, Button, Modal, ModalHeader, ModalBody, ModalFooter } from 'reactstrap';
import { useLocation, useNavigate } from 'react-router-dom';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import {
    getClientById,
    getClientApiStatusById,
    getClientBrokerDetailsById,
    getBrokerLoginActivity,
    getExecutionNodes,
    createExecutionNode,
    assignExecutionNodeToClient,
    releaseExecutionNodeFromClient,
    verifyExecutionNodeProxy,
} from '../../../../Services/Authentication';

const ClientView = () => {
    const [formData, setformData] = useState({
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        licenseType: '',
        broker: '',
        dematuserid: '',
        groupService: '',
        subadmin: '',
        status: '',
        toDate: '',
        fromDate: '',
        createdDate: '',
        strategies: [],
        segment: '',
        subSegments: [],
    });

    const [selectedTab, setSelectedTab] = useState(null);

    const location = useLocation();
    const navigate = useNavigate();

    const clientId = location.state?.clientId;
    const [apiStatus, setApiStatus] = useState({
        is_enable: null,
        username: '',
    });
    const [brokerDetails, setBrokerDetails] = useState(null);
    const [brokerLogin, setBrokerLogin] = useState(null);
    const [executionNodes, setExecutionNodes] = useState([]);
    const [selectedExecutionNodeId, setSelectedExecutionNodeId] = useState('');
    const [isNodeModalOpen, setIsNodeModalOpen] = useState(false);
    const [isNodeSaving, setIsNodeSaving] = useState(false);
    const [nodeForm, setNodeForm] = useState({
        name: '',
        execution_type: 'vps_node',
        ip_address: '',
        provider: '',
        server_url: '',
        node_id: '',
        node_secret: '',
        proxy_protocol: 'http',
        proxy_host: '',
        proxy_port: '',
        proxy_username: '',
        proxy_password: '',
        status: 'assigned',
        is_active: true,
        is_verified_with_broker: true,
        assign_now: true,
    });

    useEffect(() => {
        if (clientId) {
            fetchClientData();
            fetchClientApiStatus(clientId);
            fetchBrokerDetails(clientId);
            fetchBrokerLoginActivity(clientId)
            fetchExecutionNodes();
        }
    }, [clientId]);

    const formatDate = (dateString) => {
        if (!dateString) return '';
        const date = new Date(dateString);
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        return `${day}-${month}-${year}, ${hours}:${minutes}:${seconds}`;
    };

    const fetchClientData = async () => {
        try {
            const response = await getClientById(clientId);
            if (response) {
                const subSegments = response.client_trade_settings?.map(setting => ({
                    name: setting.sub_segment?.name || '',
                    script_name: setting.script_name || setting.sub_segment?.name || '',
                    symbol: setting.symbol || '',
                    groupService: setting.group_service || '',
                    broker: setting.broker || '',
                    product_type: setting.product_type || '',
                    order_type: setting.order_type || '',
                    buffer_percentage:
                        setting.buffer_percentage !== null && setting.buffer_percentage !== undefined
                            ? setting.buffer_percentage
                            : '',
                    quantity: setting.quantity || '',
                    sl_type: setting.sl_type || '',
                    stop_loss: setting.stop_loss || '',
                    target: setting.target || '',
                    trade_limit: setting.trade_limit || '',
                    expiry_date: formatDate(setting.expiry_date) || '',
                    max_loss_for_day: setting.max_loss_for_day || '',
                    max_profit_for_day: setting.max_profit_for_day || '',
                    is_tread_status: setting.is_tread_status ? 'On' : 'Off',
                })) || [];

                setformData({
                    firstName: response.firstName || '',
                    fullName: response.fullName || '',
                    email: response.email || '',
                    phone: response.phoneNumber || '',
                    licenseType: response.license?.name || '',
                    broker: response.Broker?.broker_name || '',
                    groupService: response.Group_service?.group_name || '',
                    dematuserid: response.demate_acc_uid || '',
                    subadmin: response.assigned_client?.fullName || '',
                    fromDate: response.start_date_client || '',
                    toDate: response.end_date_client || '',
                    createdDate: new Date(response.created_at).toLocaleString(),
                    strategies: response.Strategy?.map((s) => s.name) || [],
                    segment: "Option",
                    subSegments
                });

                // Set the first tab active by default if subSegments exist
                if (subSegments.length > 0) {
                    setSelectedTab(subSegments[0].symbol);
                }
            }
        } catch (error) {
            toast.error('Error fetching client data');
        }
    };

    const fetchClientApiStatus = async (clientId) => {
        try {
            const response = await getClientApiStatusById(clientId);
            console.log("API Status Response:", response);
            if (response) {
                setApiStatus({
                    is_enable: response.is_enable,
                    username: response.username,
                });
            }
        } catch (error) {
            console.error("Error fetching client API status:", error);
            console.error('Error fetching client API status');
        }
    };

    const fetchBrokerDetails = async (clientId) => {
        try {
            const response = await getClientBrokerDetailsById(clientId);
            if (response) {
                setBrokerDetails(response.data);
            }
        } catch (error) {
            console.error('Error fetching broker details');
        }
    };

    const fetchBrokerLoginActivity = async (clientId) => {
        try {
            const response = await getBrokerLoginActivity(clientId);
            setBrokerLogin(response?.data || null);
        } catch (error) {
            console.error('Error fetching broker login activity:', error);
        }
    };

    const fetchExecutionNodes = async () => {
        try {
            const response = await getExecutionNodes();
            const nodes = response?.results || [];
            setExecutionNodes(nodes);
            const freeNode = nodes.find((node) => !node.assigned_client);
            setSelectedExecutionNodeId(freeNode ? String(freeNode.id) : '');
        } catch (error) {
            console.error('Error fetching execution nodes:', error);
        }
    };

    const assignedExecutionNode = executionNodes.find(
        (node) => Number(node.assigned_client) === Number(clientId)
    );

    const assignableExecutionNodes = executionNodes.filter(
        (node) => !node.assigned_client || Number(node.assigned_client) === Number(clientId)
    );

    const resetNodeForm = () => {
        setNodeForm({
            name: '',
            execution_type: 'vps_node',
            ip_address: '',
            provider: '',
            server_url: '',
            node_id: '',
            node_secret: '',
            proxy_protocol: 'http',
            proxy_host: '',
            proxy_port: '',
            proxy_username: '',
            proxy_password: '',
            status: 'assigned',
            is_active: true,
            is_verified_with_broker: true,
            assign_now: true,
        });
    };

    const handleNodeFormChange = (event) => {
        const { name, value, type, checked } = event.target;
        setNodeForm((previous) => ({
            ...previous,
            [name]: type === 'checkbox' ? checked : value,
        }));
    };

    const handleAssignExistingNode = async () => {
        if (!selectedExecutionNodeId) {
            toast.error('Please select a free execution IP first.');
            return;
        }
        try {
            await assignExecutionNodeToClient(clientId, selectedExecutionNodeId);
            toast.success('Execution IP assigned to client.');
            fetchExecutionNodes();
        } catch (error) {
            toast.error(error.message || 'Failed to assign execution IP.');
        }
    };

    const handleReleaseNode = async () => {
        try {
            await releaseExecutionNodeFromClient(clientId);
            toast.success('Execution IP released from client.');
            fetchExecutionNodes();
        } catch (error) {
            toast.error(error.message || 'Failed to release execution IP.');
        }
    };

    const handleCreateNode = async () => {
        const isProxy = nodeForm.execution_type === 'proxy';
        const requiredFields = isProxy
            ? ['name', 'ip_address', 'proxy_protocol', 'proxy_host', 'proxy_port']
            : ['name', 'ip_address', 'server_url', 'node_id', 'node_secret'];
        const missingField = requiredFields.find((field) => !String(nodeForm[field] || '').trim());
        if (missingField) {
            toast.error('Please fill all required execution node fields.');
            return;
        }

        setIsNodeSaving(true);
        try {
            const payload = {
                name: nodeForm.name.trim(),
                execution_type: nodeForm.execution_type,
                ip_address: nodeForm.ip_address.trim(),
                provider: nodeForm.provider.trim(),
                status: nodeForm.status,
                is_active: nodeForm.is_active,
                is_verified_with_broker: nodeForm.is_verified_with_broker,
            };
            if (isProxy) {
                payload.proxy_protocol = nodeForm.proxy_protocol;
                payload.proxy_host = nodeForm.proxy_host.trim();
                payload.proxy_port = nodeForm.proxy_port;
                payload.proxy_username = nodeForm.proxy_username.trim();
                if (nodeForm.proxy_password) {
                    payload.proxy_password = nodeForm.proxy_password;
                }
            } else {
                payload.server_url = nodeForm.server_url.trim();
                payload.node_id = nodeForm.node_id.trim();
                payload.node_secret = nodeForm.node_secret;
            }
            const createdNode = await createExecutionNode(payload);
            if (nodeForm.assign_now) {
                await assignExecutionNodeToClient(clientId, createdNode.id);
            }
            toast.success(nodeForm.assign_now ? 'Execution IP added and assigned.' : 'Execution IP added.');
            setIsNodeModalOpen(false);
            resetNodeForm();
            fetchExecutionNodes();
        } catch (error) {
            toast.error(error.message || 'Failed to add execution IP.');
        } finally {
            setIsNodeSaving(false);
        }
    };

    const renderStatusBadge = (status) => {
        const normalized = (status || 'unavailable').toLowerCase();
        const palette = {
            active: { background: '#d1fae5', color: '#065f46', label: 'Active' },
            inactive: { background: '#fee2e2', color: '#991b1b', label: 'Inactive' },
            expired: { background: '#fee2e2', color: '#991b1b', label: 'Expired' },
            unavailable: { background: '#e5e7eb', color: '#374151', label: 'Unavailable' },
        };
        const styles = palette[normalized] || palette.unavailable;
        return (
            <span
                style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    minWidth: '110px',
                    padding: '8px 12px',
                    borderRadius: '999px',
                    backgroundColor: styles.background,
                    color: styles.color,
                    fontWeight: 600,
                }}
            >
                {styles.label}
            </span>
        );
    };

    const renderBrokerFields = () => {
        if (!brokerDetails) {
            return <p style={{ color: 'red', fontWeight: 'bold', fontSize: '18px' }}>No broker details available, First select the Broker.</p>;
        }

        const setup = brokerDetails.broker_setup;
        if (!setup) {
            return <p style={{ color: 'red', fontWeight: 'bold' }}>No broker details available.</p>;
        }

        return (
            <>
                <FormGroup className="row">
                    <Label className="col-sm-4 col-form-label">Broker Name</Label>
                    <Col sm="8">
                        <Input type="text" value={brokerDetails.selected_broker_name || brokerDetails.broker_name?.broker_name || 'not found'} readOnly />
                    </Col>
                </FormGroup>
                <FormGroup className="row">
                    <Label className="col-sm-4 col-form-label">Authentication Flow</Label>
                    <Col sm="8">
                        <Input type="text" value={(setup.auth_mode || 'unavailable').replace(/_/g, ' ')} readOnly />
                    </Col>
                </FormGroup>
                {(setup.fields || []).map((field) => (
                    <FormGroup className="row" key={field.key}>
                        <Label className="col-sm-4 col-form-label">{field.label}</Label>
                        <Col sm="8">
                            <Input
                                type="text"
                                value={
                                    field.secret
                                        ? (field.configured ? 'Saved securely' : 'Not configured')
                                        : (field.display_value || field.value || 'not found')
                                }
                                readOnly
                            />
                        </Col>
                    </FormGroup>
                ))}
                <FormGroup className="row">
                    <Label className="col-sm-4 col-form-label">Access Token</Label>
                    <Col sm="8">
                        <Input type="text" value={brokerDetails.has_access_token ? 'Available securely' : 'Unavailable'} readOnly />
                    </Col>
                </FormGroup>
                <FormGroup className="row">
                    <Label className="col-sm-4 col-form-label">Refresh Token</Label>
                    <Col sm="8">
                        <Input type="text" value={brokerDetails.has_refresh_token ? 'Available securely' : 'Unavailable'} readOnly />
                    </Col>
                </FormGroup>
                <FormGroup className="row">
                    <Label className="col-sm-4 col-form-label">Feed Token</Label>
                    <Col sm="8">
                        <Input type="text" value={brokerDetails.has_feed_token ? 'Available securely' : 'Unavailable'} readOnly />
                    </Col>
                </FormGroup>
            </>
        );
    };

    const handleTabClick = (symbol) => {
        setSelectedTab(symbol);
    };

    return (
        <Container fluid>
            <ToastContainer />
            <Row className="justify-content-center">
                <Col md="10" style={{ width: '100%' }}>
                    <Card style={{ marginTop: '30px' }}>
                        <CardBody>
                            <Row style={{ minHeight: '400px' }}>
                                {/* First Section */}
                                <h4 className="mt-4 mb-4 text-center">Client Details</h4>
                                {apiStatus.is_enable !== null && (
                                    <div
                                        className="text-center mb-4 p-3"
                                        style={{
                                            backgroundColor: apiStatus.is_enable ? 'green' : 'red',
                                            color: 'white',
                                            borderRadius: '5px',
                                            fontWeight: 'bold',
                                            fontSize: '18px'
                                        }}
                                    >
                                        {apiStatus.username} Broker is {apiStatus.is_enable ? 'Enabled' : 'Disabled'}{' '}
                                        {!apiStatus.is_enable && ', Please select the Broker.'}
                                    </div>
                                )}
                                <Col md="6" className="border-right">
                                    <Form className="theme-form mt-3">
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label">User Name</Label>
                                            <Col sm="8">
                                                <Input type="text" value={formData.firstName} readOnly placeholder="User Name" />
                                            </Col>
                                        </FormGroup>
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label">Full Name</Label>
                                            <Col sm="8">
                                                <Input type="text" value={formData.fullName} readOnly placeholder="Full Name" />
                                            </Col>
                                        </FormGroup>
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label">Email</Label>
                                            <Col sm="8">
                                                <Input type="email" value={formData.email} readOnly placeholder="Email" />
                                            </Col>
                                        </FormGroup>
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label">Phone</Label>
                                            <Col sm="8">
                                                <Input type="text" value={formData.phone} readOnly placeholder="Phone" />
                                            </Col>
                                        </FormGroup>
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label">License Type</Label>
                                            <Col sm="8">
                                                <Input type="text" value={formData.licenseType} readOnly placeholder="License" />
                                            </Col>
                                        </FormGroup>
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label">Group Service</Label>
                                            <Col sm="8">
                                                <Input type="text" value={formData.groupService} readOnly placeholder="Group Service" />
                                            </Col>
                                        </FormGroup>
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label">Client Creation Date</Label>
                                            <Col sm="8">
                                                <Input type="text" value={formData.createdDate} readOnly placeholder="Client Creation Date" />
                                            </Col>
                                        </FormGroup>
                                    </Form>
                                </Col>

                                <Col md="6">
                                    {/* Second Section */}
                                    <Form className="theme-form mt-3">
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label">Sub Segment</Label>
                                            <Col sm="8">
                                                <Input
                                                    type="text"
                                                    value={formData.subSegments.map(trade => trade.name).join(', ')}
                                                    readOnly
                                                    placeholder="Sub Segment"
                                                />
                                            </Col>
                                        </FormGroup>
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label">Segment</Label>
                                            <Col sm="8">
                                                <Input
                                                    type="text"
                                                    value={formData.segment}
                                                    readOnly
                                                    placeholder="Segment"
                                                />
                                            </Col>
                                        </FormGroup>
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label">Sub Admin</Label>
                                            <Col sm="8">
                                                <Input type="text" value={formData.subadmin} readOnly placeholder="Sub Admin" />
                                            </Col>
                                        </FormGroup>
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label">Service Start Date</Label>
                                            <Col sm="8">
                                                <Input type="date" value={formData.fromDate} placeholder="Service Start Date" readOnly />
                                            </Col>
                                        </FormGroup>
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label">Service End Date</Label>
                                            <Col sm="8">
                                                <Input type="date" value={formData.toDate} placeholder="Service End Date" readOnly />
                                            </Col>
                                        </FormGroup>
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label">Strategy</Label>
                                            <Col sm="8">
                                                <Input
                                                    type="text"
                                                    value={formData.strategies.join(', ')}
                                                    readOnly
                                                    placeholder="Strategies"
                                                />
                                            </Col>
                                        </FormGroup>
                                    </Form>
                                </Col>
                            </Row>
                            <br />
                            <Row className='mt-4'>
                                <Col md="6" className="border-right mb-4">
                                    <h4 className="mt-4 mb-4 text-left">Client Broker Details</h4>
                                    <Form className="theme-form mt-3">
                                        {renderBrokerFields()}
                                    </Form>
                                </Col>

                                <Col md="6" className="mb-4">
                                    <h4 className="mt-4 mb-4 text-left">Login Activity</h4>
                                    <Form className="theme-form mt-3">
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label">Panel Login Time</Label>
                                            <Col sm="8">
                                                <Input
                                                    type="text"
                                                    value={brokerLogin?.panel?.current_panel_login_time
                                                        ? formatDate(brokerLogin.panel.current_panel_login_time)
                                                        : (brokerLogin?.panel?.panel_login_time ? formatDate(brokerLogin.panel.panel_login_time) : 'Unavailable')}
                                                    readOnly
                                                />
                                            </Col>
                                        </FormGroup>
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label">Panel Logout Time</Label>
                                            <Col sm="8">
                                                <Input
                                                    type="text"
                                                    value={brokerLogin?.panel?.panel_logout_time ? formatDate(brokerLogin.panel.panel_logout_time) : 'Unavailable'}
                                                    readOnly
                                                />
                                            </Col>
                                        </FormGroup>
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label">Broker Session</Label>
                                            <Col sm="8">
                                                <div>{renderStatusBadge(brokerLogin?.broker?.session?.status)}</div>
                                            </Col>
                                        </FormGroup>
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label">Broker Token</Label>
                                            <Col sm="8">
                                                <div>{renderStatusBadge(brokerLogin?.broker?.token?.status)}</div>
                                            </Col>
                                        </FormGroup>
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label">Token Expiry</Label>
                                            <Col sm="8">
                                                <Input
                                                    type="text"
                                                    value={brokerLogin?.broker?.token?.expires_at ? formatDate(brokerLogin.broker.token.expires_at) : 'Unavailable'}
                                                    readOnly
                                                />
                                            </Col>
                                        </FormGroup>
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label">Broker Last Login</Label>
                                            <Col sm="8">
                                                <Input
                                                    type="text"
                                                    value={brokerLogin?.broker?.last_login_at ? formatDate(brokerLogin.broker.last_login_at) : 'Unavailable'}
                                                    readOnly
                                                />
                                            </Col>
                                        </FormGroup>
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label">Broker Last Logout</Label>
                                            <Col sm="8">
                                                <Input
                                                    type="text"
                                                    value={brokerLogin?.broker?.last_logout_at ? formatDate(brokerLogin.broker.last_logout_at) : 'Unavailable'}
                                                    readOnly
                                                />
                                            </Col>
                                        </FormGroup>
                                    </Form>
                                </Col>
                            </Row>
                            <Row className='mt-4'>
                                <Col md="12" className="mb-4">
                                    <div
                                        style={{
                                            border: '1px solid #e5e7eb',
                                            borderRadius: '8px',
                                            padding: '20px',
                                            backgroundColor: '#ffffff',
                                        }}
                                    >
                                        <div className="d-flex justify-content-between align-items-center mb-3">
                                            <div>
                                                <h4 className="mb-1">Static Execution IP</h4>
                                                <p className="mb-0" style={{ color: '#6b7280' }}>
                                                    Assign the client to the VPS/IP that will place broker orders.
                                                </p>
                                            </div>
                                            <Button
                                                className="btn btn-primary search-btn-clr"
                                                onClick={() => setIsNodeModalOpen(true)}
                                            >
                                                Add IP
                                            </Button>
                                        </div>

                                        {assignedExecutionNode ? (
                                            <Row>
                                                <Col md="3">
                                                    <Label>Node Name</Label>
                                                    <Input type="text" value={assignedExecutionNode.name || 'Unavailable'} readOnly />
                                                </Col>
                                                <Col md="2">
                                                    <Label>Static IP</Label>
                                                    <Input type="text" value={assignedExecutionNode.ip_address || 'Unavailable'} readOnly />
                                                </Col>
                                                <Col md="3">
                                                    <Label>Server URL</Label>
                                                    <Input type="text" value={assignedExecutionNode.server_url || 'Unavailable'} readOnly />
                                                </Col>
                                                <Col md="2">
                                                    <Label>Status</Label>
                                                    <Input
                                                        type="text"
                                                        value={`${assignedExecutionNode.status || 'unavailable'}${assignedExecutionNode.is_verified_with_broker ? ' / verified' : ' / not verified'}`}
                                                        readOnly
                                                    />
                                                </Col>
                                                <Col md="2" className="d-flex align-items-end">
                                                    <Button color="danger" outline onClick={handleReleaseNode} style={{ width: '100%' }}>
                                                        Release
                                                    </Button>
                                                </Col>
                                            </Row>
                                        ) : (
                                            <Row className="align-items-end">
                                                <Col md="8">
                                                    <Label>Assign Existing Free IP</Label>
                                                    <Input
                                                        type="select"
                                                        value={selectedExecutionNodeId}
                                                        onChange={(event) => setSelectedExecutionNodeId(event.target.value)}
                                                    >
                                                        <option value="">Select execution IP</option>
                                                        {assignableExecutionNodes.map((node) => (
                                                            <option key={node.id} value={node.id}>
                                                                {node.name} - {node.ip_address} ({node.status})
                                                            </option>
                                                        ))}
                                                    </Input>
                                                </Col>
                                                <Col md="4">
                                                    <Button
                                                        className="btn btn-primary search-btn-clr"
                                                        onClick={handleAssignExistingNode}
                                                        disabled={!selectedExecutionNodeId}
                                                        style={{ width: '100%' }}
                                                    >
                                                        Assign IP to Client
                                                    </Button>
                                                </Col>
                                                <Col md="12" className="mt-3">
                                                    <p className="mb-0" style={{ color: '#991b1b', fontWeight: 600 }}>
                                                        No static execution IP is assigned to this client. Live routed orders will be blocked until one verified node is assigned.
                                                    </p>
                                                </Col>
                                            </Row>
                                        )}
                                    </div>
                                </Col>
                            </Row>
                            <Row className='mt-4'>
                                {/* Left Column - Tabs */}
                                <Col xs="12" sm="6" md="5" style={{ paddingRight: '30px' }}>
                                    <h5 className='mb-3'>Trade Symbols</h5>
                                    {formData.subSegments.filter(trade => trade.symbol).length > 0 ? (
                                        <ul className="list-group">
                                            {formData.subSegments
                                                .filter(trade => trade.symbol)
                                                .map((trade, index) => (
                                                    <li
                                                        key={index}
                                                        className={`${selectedTab === trade.symbol ? 'active' : ''}`}
                                                        onClick={() => handleTabClick(trade.symbol)}
                                                        style={{
                                                            borderRadius: '3px',
                                                            cursor: 'pointer',
                                                            padding: '12px 16px',
                                                            fontSize: '16px',
                                                            height: '50px',
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            background: selectedTab === trade.symbol ? '#283F7B' : 'white',
                                                            color: selectedTab === trade.symbol ? 'white' : 'black',
                                                            border: '1px solid #ccc',
                                                            transition: 'background 0.3s ease'
                                                        }}
                                                    >
                                                        {trade.symbol}
                                                    </li>
                                                ))}
                                        </ul>
                                    ) : (
                                        <p style={{ color: 'red', fontWeight: 'bold', fontSize: '18px' }}>
                                            No Trade Symbol is available, First Update the Trade Symbol.
                                        </p>
                                    )}
                                </Col>

                                {/* Right Column - Trade Settings Form */}
                                <Col xs="12" sm="6" md="7">
                                    {selectedTab && formData.subSegments.map((trade, index) => (
                                        trade.symbol === selectedTab && (
                                            <div key={index}>
                                                <h5 className='mb-3'>Trade Settings for {selectedTab}</h5>
                                                <Form className="theme-form mt-3">
                                                    <Row>
                                                        <Col md="6">
                                                            <FormGroup className="row">
                                                                <Label className="col-sm-4 col-form-label">Script</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.script_name || trade.name || 'not found'} readOnly />
                                                                </Col>
                                                            </FormGroup>
                                                            <FormGroup className="row">
                                                                <Label className="col-sm-4 col-form-label">Group Service</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.groupService || 'not found'} readOnly />
                                                                </Col>
                                                            </FormGroup>
                                                            <FormGroup className="row">
                                                                <Label className="col-sm-4 col-form-label">Broker</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.broker || 'not found'} readOnly />
                                                                </Col>
                                                            </FormGroup>
                                                            <FormGroup className="row">
                                                                <Label className="col-sm-4 col-form-label">Product Type</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.product_type || 'not found'} readOnly />
                                                                </Col>
                                                            </FormGroup>
                                                            <FormGroup className="row">
                                                                <Label className="col-sm-4 col-form-label">Order Type</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.order_type || 'not found'} readOnly />
                                                                </Col>
                                                            </FormGroup>
                                                            <FormGroup className="row">
                                                                <Label className="col-sm-4 col-form-label">Buffer %</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.buffer_percentage || 'not found'} readOnly />
                                                                </Col>
                                                            </FormGroup>
                                                            <FormGroup className="row">
                                                                <Label className="col-sm-4 col-form-label">Expiry Date</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.expiry_date || 'not found'} readOnly />
                                                                </Col>
                                                            </FormGroup>
                                                        </Col>

                                                        <Col md="6">
                                                            <FormGroup className="row">
                                                                <Label className="col-sm-4 col-form-label">Trade Status</Label>
                                                                <Col sm="8">
                                                                    <Input
                                                                        type="text"
                                                                        value={trade.is_tread_status || 'not found'}
                                                                        readOnly
                                                                        style={{ color: trade.is_tread_status === 'On' ? 'green' : 'red', fontWeight: 'bold', fontSize: '20px' }}
                                                                    />
                                                                </Col>
                                                            </FormGroup>

                                                            <FormGroup className="row">
                                                                <Label className="col-sm-4 col-form-label">Trade Limit</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.trade_limit || 'not found'} readOnly />
                                                                </Col>
                                                            </FormGroup>
                                                            <FormGroup className="row">
                                                                <Label className="col-sm-4 col-form-label">Quantity</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.quantity || 'not found'} readOnly />
                                                                </Col>
                                                            </FormGroup>
                                                            <FormGroup className="row">
                                                                <Label className="col-sm-4 col-form-label">SL-TP Type</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.sl_type || 'not found'} readOnly />
                                                                </Col>
                                                            </FormGroup>
                                                            <FormGroup className="row">
                                                                <Label className="col-sm-4 col-form-label">Stop Loss</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.stop_loss || 'not found'} readOnly />
                                                                </Col>
                                                            </FormGroup>
                                                            <FormGroup className="row">
                                                                <Label className="col-sm-4 col-form-label">Target</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.target || 'not found'} readOnly />
                                                                </Col>
                                                            </FormGroup>
                                                            <FormGroup className="row">
                                                                <Label className="col-sm-4 col-form-label">Max Profit For Day</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.max_profit_for_day || 'not found'} readOnly />
                                                                </Col>
                                                            </FormGroup>
                                                            <FormGroup className="row">
                                                                <Label className="col-sm-4 col-form-label">Max Loss For Day</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.max_loss_for_day || 'not found'} readOnly />
                                                                </Col>
                                                            </FormGroup>
                                                        </Col>
                                                    </Row>
                                                </Form>
                                            </div>
                                        )
                                    ))}
                                </Col>
                            </Row>

                            {/* Common Back Button */}
                            <Row className="justify-content-center mt-4">
                                <Col sm="auto">
                                    <Button
                                        className="btn btn-primary search-btn-clr"
                                        onClick={() => navigate('/client/all-clients-list')}
                                    >
                                        Back
                                    </Button>
                                </Col>
                            </Row>
                        </CardBody>
                    </Card>
                </Col>
            </Row>
            <Modal isOpen={isNodeModalOpen} toggle={() => setIsNodeModalOpen(false)} size="lg">
                <ModalHeader toggle={() => setIsNodeModalOpen(false)}>Add Static Execution IP</ModalHeader>
                <ModalBody>
                    <Form>
                        <Row>
                            <Col md="12">
                                <FormGroup>
                                    <Label>Execution Type *</Label>
                                    <Input type="select" name="execution_type" value={nodeForm.execution_type} onChange={handleNodeFormChange}>
                                        <option value="vps_node">VPS Node</option>
                                        <option value="proxy">Proxy IP</option>
                                    </Input>
                                </FormGroup>
                            </Col>
                            <Col md="6">
                                <FormGroup>
                                    <Label>Node Name *</Label>
                                    <Input
                                        name="name"
                                        value={nodeForm.name}
                                        onChange={handleNodeFormChange}
                                        placeholder="Client VPS Mumbai 1"
                                    />
                                </FormGroup>
                            </Col>
                            <Col md="6">
                                <FormGroup>
                                    <Label>Static IP *</Label>
                                    <Input
                                        name="ip_address"
                                        value={nodeForm.ip_address}
                                        onChange={handleNodeFormChange}
                                        placeholder="3.109.40.137"
                                    />
                                </FormGroup>
                            </Col>
                        </Row>
                        <Row>
                            <Col md="6">
                                <FormGroup>
                                    <Label>Provider</Label>
                                    <Input
                                        name="provider"
                                        value={nodeForm.provider}
                                        onChange={handleNodeFormChange}
                                        placeholder="AWS"
                                    />
                                </FormGroup>
                            </Col>
                        </Row>
                        {nodeForm.execution_type === 'vps_node' ? (
                            <>
                                <Row>
                                    <Col md="6">
                                        <FormGroup>
                                            <Label>Node ID *</Label>
                                            <Input name="node_id" value={nodeForm.node_id} onChange={handleNodeFormChange} placeholder="client-ashutosh-node-1" />
                                        </FormGroup>
                                    </Col>
                                    <Col md="6">
                                        <FormGroup>
                                            <Label>Server URL *</Label>
                                            <Input name="server_url" value={nodeForm.server_url} onChange={handleNodeFormChange} placeholder="https://node1.example.com" />
                                        </FormGroup>
                                    </Col>
                                </Row>
                                <FormGroup>
                                    <Label>Node Secret *</Label>
                                    <Input type="password" name="node_secret" value={nodeForm.node_secret} onChange={handleNodeFormChange} placeholder="Shared HMAC secret for this execution node" />
                                </FormGroup>
                            </>
                        ) : (
                            <>
                                <Row>
                                    <Col md="4">
                                        <FormGroup>
                                            <Label>Proxy Protocol *</Label>
                                            <Input type="select" name="proxy_protocol" value={nodeForm.proxy_protocol} onChange={handleNodeFormChange}>
                                                <option value="http">HTTP</option>
                                                <option value="https">HTTPS</option>
                                                <option value="socks5">SOCKS5</option>
                                            </Input>
                                        </FormGroup>
                                    </Col>
                                    <Col md="5">
                                        <FormGroup>
                                            <Label>Proxy Host *</Label>
                                            <Input name="proxy_host" value={nodeForm.proxy_host} onChange={handleNodeFormChange} placeholder="proxy.vendor.com" />
                                        </FormGroup>
                                    </Col>
                                    <Col md="3">
                                        <FormGroup>
                                            <Label>Proxy Port *</Label>
                                            <Input name="proxy_port" value={nodeForm.proxy_port} onChange={handleNodeFormChange} placeholder="8080" />
                                        </FormGroup>
                                    </Col>
                                </Row>
                                <Row>
                                    <Col md="6">
                                        <FormGroup>
                                            <Label>Proxy Username</Label>
                                            <Input name="proxy_username" value={nodeForm.proxy_username} onChange={handleNodeFormChange} autoComplete="off" />
                                        </FormGroup>
                                    </Col>
                                    <Col md="6">
                                        <FormGroup>
                                            <Label>Proxy Password</Label>
                                            <Input type="password" name="proxy_password" value={nodeForm.proxy_password} onChange={handleNodeFormChange} autoComplete="off" />
                                        </FormGroup>
                                    </Col>
                                </Row>
                            </>
                        )}
                        <Row>
                            <Col md="4">
                                <FormGroup check>
                                    <Input
                                        type="checkbox"
                                        name="is_active"
                                        checked={nodeForm.is_active}
                                        onChange={handleNodeFormChange}
                                    />
                                    <Label check>Active</Label>
                                </FormGroup>
                            </Col>
                            <Col md="4">
                                <FormGroup check>
                                    <Input
                                        type="checkbox"
                                        name="is_verified_with_broker"
                                        checked={nodeForm.is_verified_with_broker}
                                        onChange={handleNodeFormChange}
                                    />
                                    <Label check>Broker IP verified</Label>
                                </FormGroup>
                            </Col>
                            <Col md="4">
                                <FormGroup check>
                                    <Input
                                        type="checkbox"
                                        name="assign_now"
                                        checked={nodeForm.assign_now}
                                        onChange={handleNodeFormChange}
                                    />
                                    <Label check>Assign to this client</Label>
                                </FormGroup>
                            </Col>
                        </Row>
                    </Form>
                </ModalBody>
                <ModalFooter>
                    <Button color="secondary" outline onClick={() => setIsNodeModalOpen(false)} disabled={isNodeSaving}>
                        Cancel
                    </Button>
                    <Button className="btn btn-primary search-btn-clr" onClick={handleCreateNode} disabled={isNodeSaving}>
                        {isNodeSaving ? 'Saving...' : 'Add IP'}
                    </Button>
                </ModalFooter>
            </Modal>
        </Container>
    );
};

export default ClientView;
