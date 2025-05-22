import React, { useEffect, useState } from 'react';
import { Container, Row, Col, Card, CardBody, Form, FormGroup, Label, Input, Button } from 'reactstrap';
import { useLocation, useNavigate } from 'react-router-dom';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { getClientById, getClientApiStatusById, getClientBrokerDetailsById, getBrokerLoginActivity } from '../../../../Services/Authentication';

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

    useEffect(() => {
        if (clientId) {
            fetchClientData();
            fetchClientApiStatus(clientId);
            fetchBrokerDetails(clientId);
            fetchBrokerLoginActivity(clientId)
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
                    symbol: setting.symbol || '',
                    strategy: setting.strategy || '',
                    groupService: setting.group_service || '',
                    broker: setting.broker || '',
                    product_type: setting.product_type || '',
                    buy_sell: setting.buy_sell || '',
                    quantity: setting.quantity || '',
                    sl_type: setting.sl_type || '',
                    stop_loss: setting.stop_loss || '',
                    target: setting.target || '',
                    trade_limit: setting.trade_limit || '',
                    expiry_date: formatDate(setting.expiry_date) || '',
                    max_loss_for_day: setting.max_loss_for_day || '',
                    min_loss_for_day: setting.min_loss_for_day || '',
                    max_profit_for_day: setting.max_profit_for_day || '',
                    min_profit_for_day: setting.min_profit_for_day || '',
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
            if (response && response.length > 0) {
                const loginActivity = response[0];
                const formattedLoginActivity = {
                    last_login: formatDate(loginActivity.last_login),
                    logout_time: loginActivity.logout_time ? formatDate(loginActivity.logout_time) : 'not found',
                    isTokenExpired: loginActivity.isTokenExpired,
                };
                setBrokerLogin(formattedLoginActivity);
            } else {
                setBrokerLogin(null);
            }
        } catch (error) {
            console.error('Error fetching broker login activity:', error);
        }
    };

    const renderBrokerFields = () => {
        if (!brokerDetails) {
            return <p style={{ color: 'red', fontWeight: 'bold', fontSize: '18px' }}>No broker details available, First select the Broker.</p>;
        }

        const {
            broker_name,
            broker_API_SKEY,
            broker_API_KEY,
            broker_API_UID,
            broker_Demate_User_Name,
            broker_Totp_Authcode,
            broker_pass,
            access_token,
            request_token
        } = brokerDetails;

        const brokerName = broker_name?.broker_name.toLowerCase();

        const commonFields = (
            <>
                <FormGroup className="row">
                    <Label className="col-sm-4 col-form-label">Access Token</Label>
                    <Col sm="8">
                        <Input type="text" value={access_token || 'not found'} readOnly />
                    </Col>
                </FormGroup>
                <FormGroup className="row">
                    <Label className="col-sm-4 col-form-label">Request Token</Label>
                    <Col sm="8">
                        <Input type="text" value={request_token || 'not found'} readOnly />
                    </Col>
                </FormGroup>
            </>
        );

        switch (brokerName) {
            case 'upstox':
                return (
                    <>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">Broker Name</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_name.broker_name || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">API SKEY</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_API_SKEY || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">API KEY</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_API_KEY || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        {commonFields}
                    </>
                );
            case 'alice blue':
                return (
                    <>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">Broker Name</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_name.broker_name || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">API KEY</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_API_KEY || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">API UID</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_API_UID || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        {commonFields}
                    </>
                );
            case 'angle one':
                return (
                    <>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">Broker Name</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_name.broker_name || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">API KEY</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_API_KEY || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">TOTP Authcode</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_Totp_Authcode || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">Password</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_pass || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">Demat User Name</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_Demate_User_Name || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        {commonFields}
                    </>
                );
            case 'zerodha':
                return (
                    <>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">Broker Name</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_name.broker_name || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">API SKEY</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_API_SKEY || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">API KEY</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_API_KEY || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        {commonFields}
                    </>
                );
            case '5paisa':
                return (
                    <>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">Broker Name</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_name.broker_name || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">API SKEY</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_API_SKEY || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">API KEY</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_API_KEY || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">API UID</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_API_UID || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        {commonFields}
                    </>
                );
            case 'dhan':
                return (
                    <>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">Broker Name</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_name.broker_name || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">API KEY</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_API_KEY || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        {commonFields}
                    </>
                );
            case 'fyers':
                return (
                    <>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">Broker Name</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_name.broker_name || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">API KEY</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_API_KEY || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        <FormGroup className="row">
                            <Label className="col-sm-4 col-form-label">API KEY</Label>
                            <Col sm="8">
                                <Input type="text" value={broker_API_SKEY || 'not found'} readOnly />
                            </Col>
                        </FormGroup>
                        {commonFields}
                    </>
                );
            default:
                return <p style={{ color: 'red', fontWeight: 'bold' }}>No broker details available.</p>;
        }
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
                                            <Label className="col-sm-4 col-form-label">Create Date</Label>
                                            <Col sm="8">
                                                <Input type="text" value={formData.createdDate} readOnly placeholder="Create Date" />
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
                                            <Label className="col-sm-4 col-form-label">Start Date</Label>
                                            <Col sm="8">
                                                <Input type="date" value={formData.fromDate} placeholder="From Date" readOnly />
                                            </Col>
                                        </FormGroup>
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label">End Date</Label>
                                            <Col sm="8">
                                                <Input type="date" value={formData.toDate} placeholder="To Date" readOnly />
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
                                    <h4 className="mt-4 mb-4 text-left">Broker Login Activity</h4>
                                    <Form className="theme-form mt-3">
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label" for="lastLogin">Last Login</Label>
                                            <Col sm="8">
                                                <Input
                                                    type="text"
                                                    id="lastLogin"
                                                    value={brokerLogin ? brokerLogin.last_login : 'not found'}
                                                    readOnly
                                                    placeholder="Last Login Time"
                                                />
                                            </Col>
                                        </FormGroup>
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label" for="logoutTime">Logout Time</Label>
                                            <Col sm="8">
                                                <Input
                                                    type="text"
                                                    id="logoutTime"
                                                    value={brokerLogin ? brokerLogin.logout_time : 'not found'}
                                                    readOnly
                                                    placeholder="Logout Time"
                                                />
                                            </Col>
                                        </FormGroup>
                                        <FormGroup className="row">
                                            <Label className="col-sm-4 col-form-label" for="tokenExpired">Token Expired</Label>
                                            <Col sm="8">
                                                <Input
                                                    type="text"
                                                    readOnly
                                                    value={
                                                        brokerLogin === null
                                                            ? 'Not found'
                                                            : brokerLogin.isTokenExpired === null
                                                                ? 'Not Logged In'
                                                                : brokerLogin.isTokenExpired
                                                                    ? 'Token Expired'
                                                                    : 'Not Expired'
                                                    }
                                                    style={{
                                                        color:
                                                            brokerLogin === null
                                                                ? 'gray'
                                                                : brokerLogin.isTokenExpired === null
                                                                    ? 'orange'
                                                                    : brokerLogin.isTokenExpired
                                                                        ? 'red'
                                                                        : 'green',
                                                        fontWeight: 'bold',
                                                        backgroundColor: 'transparent',
                                                    }}
                                                />
                                            </Col>
                                        </FormGroup>
                                    </Form>
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
                                                    {/* Left Section - First 5 Input Fields */}
                                                    <Row>
                                                        <Col md="6">
                                                            <FormGroup className="row">
                                                                <Label className="col-sm-4 col-form-label">Name</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.name || 'not found'} readOnly />
                                                                </Col>
                                                            </FormGroup>
                                                            <FormGroup className="row">
                                                                <Label className="col-sm-4 col-form-label">Group Service</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.groupService || 'not found'} readOnly />
                                                                </Col>
                                                            </FormGroup>
                                                            {/* <FormGroup className="row">
                                                                <Label className="col-sm-4 col-form-label">Strategy</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.strategy || ''} readOnly />
                                                                </Col>
                                                            </FormGroup> */}
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
                                                                <Label className="col-sm-4 col-form-label">Buy/Sell</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.buy_sell || 'not found'} readOnly />
                                                                </Col>
                                                            </FormGroup>
                                                            <FormGroup className="row">
                                                                <Label className="col-sm-4 col-form-label">Expiry Date</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.expiry_date || 'not found'} readOnly />
                                                                </Col>
                                                            </FormGroup>
                                                            <FormGroup className="row">
                                                                <Label className="col-sm-4 col-form-label">Max Profit For Day</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.max_profit_for_day || 'not found'} readOnly />
                                                                </Col>
                                                            </FormGroup>
                                                            <FormGroup className="row">
                                                                <Label className="col-sm-4 col-form-label">Min Profit For Day</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.min_profit_for_day || 'not found'} readOnly />
                                                                </Col>
                                                            </FormGroup>
                                                        </Col>

                                                        {/* Right Section - Last 5 Input Fields */}
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
                                                                <Label className="col-sm-4 col-form-label">SL Type</Label>
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
                                                                <Label className="col-sm-4 col-form-label">Max Loss For Day</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.max_loss_for_day || 'not found'} readOnly />
                                                                </Col>
                                                            </FormGroup>
                                                            <FormGroup className="row">
                                                                <Label className="col-sm-4 col-form-label">Min Loss For Day</Label>
                                                                <Col sm="8">
                                                                    <Input type="text" value={trade.min_loss_for_day || 'not found'} readOnly />
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
        </Container>
    );
};

export default ClientView;
