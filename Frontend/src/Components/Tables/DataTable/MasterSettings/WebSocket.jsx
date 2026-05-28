import React, { useState, useEffect } from 'react';
import {
    Col,
    Card,
    CardHeader,
    CardBody,
    Form,
    Label,
    Row,
    Input,
    Button,
    Spinner
} from 'reactstrap';
import { ToastContainer, toast } from 'react-toastify';
import Swal from 'sweetalert2';
import 'react-toastify/dist/ReactToastify.css';
import {
    connectMarketDataUpstox,
    getExecutionNodes,
    getMarketDataUpstoxSettings,
    updateMarketDataUpstoxSettings,
    updateWebSocket,
    getWebsocket,
} from '../../../../Services/Authentication';

const WebSocket = () => {
    const [socketDetails, setSocketDetails] = useState({
        auth_token: '',
        token_status: '',
        status: '',
    });

    const [errors, setErrors] = useState({});
    const [loading, setLoading] = useState(false);
    const [marketData, setMarketData] = useState({
        api_key: '',
        api_secret: '',
        api_secret_configured: false,
        execution_node: '',
        token_status: '',
        token_configured: false,
        access_token_expiry: '',
        is_active: true,
    });
    const [executionNodes, setExecutionNodes] = useState([]);
    const [marketLoading, setMarketLoading] = useState(false);

    useEffect(() => {
        fetchSocketDetails();
        fetchMarketDataSettings();
        fetchExecutionNodes();
    }, []);

    const fetchSocketDetails = async () => {
        try {
            const response = await getWebsocket();
            console.log("getWebsocket response:", response);

            setSocketDetails({
                auth_token: response.auth_token || '',
                token_status: response.token_status || '',
                status: response.status || '',
            });
        } catch (error) {
            console.error('Error in fetchSocketDetails:', error.message || 'Something went wrong while fetching WebSocket details');
        }
    };

    const fetchExecutionNodes = async () => {
        try {
            const response = await getExecutionNodes();
            setExecutionNodes(response.results || []);
        } catch (error) {
            console.error('Error fetching execution routes:', error.message || error);
        }
    };

    const fetchMarketDataSettings = async () => {
        try {
            const response = await getMarketDataUpstoxSettings();
            const data = response.data || {};
            setMarketData({
                api_key: data.api_key || '',
                api_secret: '',
                api_secret_configured: Boolean(data.api_secret_configured),
                execution_node: data.execution_node || '',
                token_status: data.token_status || '',
                token_configured: Boolean(data.token_configured),
                access_token_expiry: data.access_token_expiry || '',
                is_active: data.is_active !== false,
            });
        } catch (error) {
            console.error('Error fetching market data settings:', error.message || error);
        }
    };

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setSocketDetails((prevData) => ({
            ...prevData,
            [name]: type === "checkbox" ? checked : value,
            // Reset the status if they modify auth_token
            ...(name === 'auth_token' ? { status: '', token_status: '' } : {}),
        }));
        setErrors((prevErrors) => ({ ...prevErrors, [name]: '' }));
    };
    

    const validateForm = () => {
        const newErrors = {};
        if (!socketDetails.auth_token) {
            newErrors.auth_token = 'Auth Token is required';
        }
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!validateForm()) {
            Object.values(errors).forEach((error) => {
                Swal.fire('Validation Error', error, 'error');
            });
            return;
        }

        if (socketDetails.status === 'failed') {
            Swal.fire('Update Blocked', 'Token status is inactive. Please check your token.', 'warning');
            return;
        }

        setLoading(true);
        try {
            const response = await updateWebSocket({ auth_token: socketDetails.auth_token });

            if (response.status === 'success') {
                toast.success(response.message || 'WebSocket token updated successfully');
                setSocketDetails((prev) => ({
                    ...prev,
                    token_status: response.data.token_status || '',
                    status: response.status || '',
                }));
            } else {
                toast.error(response.message || 'Failed to update WebSocket token');
            }
        } catch (error) {
            toast.error(error.message || 'An error occurred while updating WebSocket token');
        } finally {
            setLoading(false);
        }
    };

    const handleMarketDataChange = (e) => {
        const { name, value, type, checked } = e.target;
        setMarketData((previous) => ({
            ...previous,
            [name]: type === 'checkbox' ? checked : value,
        }));
    };

    const handleMarketDataSave = async (e) => {
        e.preventDefault();
        if (!marketData.api_key) {
            Swal.fire('Validation Error', 'Upstox API Key is required.', 'error');
            return;
        }
        if (!marketData.api_secret_configured && !marketData.api_secret) {
            Swal.fire('Validation Error', 'Upstox API Secret Key is required.', 'error');
            return;
        }
        if (!marketData.execution_node) {
            Swal.fire('Validation Error', 'Please select an execution route.', 'error');
            return;
        }

        setMarketLoading(true);
        try {
            const payload = {
                api_key: marketData.api_key,
                execution_node: marketData.execution_node,
                is_active: marketData.is_active,
            };
            if (marketData.api_secret) {
                payload.api_secret = marketData.api_secret;
            }
            const response = await updateMarketDataUpstoxSettings(payload);
            toast.success(response.message || 'Market data account saved.');
            const data = response.data || {};
            setMarketData((previous) => ({
                ...previous,
                api_secret: '',
                api_secret_configured: Boolean(data.api_secret_configured),
                token_status: data.token_status || previous.token_status,
                token_configured: Boolean(data.token_configured),
                access_token_expiry: data.access_token_expiry || '',
            }));
        } catch (error) {
            toast.error(error.message || 'Failed to save market data account.');
        } finally {
            setMarketLoading(false);
        }
    };

    const handleMarketDataConnect = async () => {
        setMarketLoading(true);
        try {
            const response = await connectMarketDataUpstox();
            if (response.redirect_url) {
                window.location.assign(response.redirect_url);
                return;
            }
            toast.error(response.message || 'Upstox did not return a login URL.');
        } catch (error) {
            toast.error(error.message || 'Failed to start Upstox login.');
        } finally {
            setMarketLoading(false);
        }
    };

    const formatDateTime = (value) => {
        if (!value) return '';
        try {
            return new Date(value).toLocaleString();
        } catch {
            return value;
        }
    };

    return (
        <>
            <ToastContainer />
            <Col sm="12">
                <Card className="mt-5">
                    <CardHeader>
                        <h5>Update WebSocket Details</h5>
                    </CardHeader>
                    <CardBody>
                        <Form className="needs-validation mt-3" noValidate onSubmit={handleSubmit}>
                            <Row>
                                <Col md="12" className="mb-6">
                                    <Label htmlFor="auth_token">
                                        Auth Token <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                                    </Label>
                                    <Input
                                        type="textarea"
                                        style={{ height: '100px', maxHeight: '200px' }}
                                        className={`form-control ${errors.auth_token ? 'is-invalid' : ''}`}
                                        name="auth_token"
                                        id="auth_token"
                                        placeholder="Enter Auth Token"
                                        value={socketDetails.auth_token}
                                        onChange={handleChange}
                                        required
                                    />
                                    {errors.auth_token && (
                                        <div className="invalid-feedback text-danger">{errors.auth_token}</div>
                                    )}
                                </Col>
                            </Row>
                            <Row className='mt-4'>
                                <Col md="4" className="mb-3">
                                    <Label htmlFor="token_status">
                                        Token Status
                                    </Label>
                                    <Input
                                        type="text"
                                        className="form-control"
                                        name="token_status"
                                        id="token_status"
                                        placeholder="Token Status"
                                        value={socketDetails.token_status}
                                        readOnly
                                        disabled
                                        style={{
                                            color:
                                                socketDetails.status === 'failed' ? 'red' :
                                                    socketDetails.status === 'success' ? 'green' :
                                                        'inherit',
                                            fontWeight: 'bold',
                                        }}
                                    />
                                </Col>
                            </Row>

                            <Button color="primary" type="submit" className="mt-4 search-btn-clr" disabled={loading}>
                                {loading ? <Spinner size="sm" /> : 'Save'}
                            </Button>
                        </Form>
                    </CardBody>
                </Card>
            </Col>
            <Col sm="12">
                <Card className="mt-4">
                    <CardHeader>
                        <h5>Upstox Market Data Account</h5>
                    </CardHeader>
                    <CardBody>
                        <Form className="needs-validation mt-3" noValidate onSubmit={handleMarketDataSave}>
                            <Row>
                                <Col md="6" className="mb-3">
                                    <Label htmlFor="market_api_key">API Key <span style={{ color: 'red' }}>*</span></Label>
                                    <Input
                                        type="password"
                                        name="api_key"
                                        id="market_api_key"
                                        value={marketData.api_key}
                                        onChange={handleMarketDataChange}
                                        placeholder="Enter Upstox API Key"
                                    />
                                </Col>
                                <Col md="6" className="mb-3">
                                    <Label htmlFor="market_api_secret">API Secret Key {marketData.api_secret_configured ? '' : <span style={{ color: 'red' }}>*</span>}</Label>
                                    <Input
                                        type="password"
                                        name="api_secret"
                                        id="market_api_secret"
                                        value={marketData.api_secret}
                                        onChange={handleMarketDataChange}
                                        placeholder={marketData.api_secret_configured ? 'Leave blank to keep saved secret' : 'Enter Upstox API Secret Key'}
                                    />
                                </Col>
                            </Row>
                            <Row>
                                <Col md="6" className="mb-3">
                                    <Label htmlFor="market_execution_node">Execution Route <span style={{ color: 'red' }}>*</span></Label>
                                    <Input
                                        type="select"
                                        name="execution_node"
                                        id="market_execution_node"
                                        value={marketData.execution_node}
                                        onChange={handleMarketDataChange}
                                    >
                                        <option value="">Select route</option>
                                        {executionNodes.map((node) => (
                                            <option key={node.id} value={node.id}>
                                                {node.name} - {node.execution_type || 'route'} {node.proxy_public_ip_verified ? '(verified)' : ''}
                                            </option>
                                        ))}
                                    </Input>
                                </Col>
                                <Col md="3" className="mb-3">
                                    <Label>Token Status</Label>
                                    <Input
                                        type="text"
                                        value={marketData.token_configured ? marketData.token_status || 'active' : 'not generated'}
                                        readOnly
                                        disabled
                                        style={{
                                            color: marketData.token_status === 'active' ? 'green' : 'red',
                                            fontWeight: 'bold',
                                        }}
                                    />
                                </Col>
                                <Col md="3" className="mb-3">
                                    <Label>Token Expiry</Label>
                                    <Input type="text" value={formatDateTime(marketData.access_token_expiry)} readOnly disabled />
                                </Col>
                            </Row>
                            <Row>
                                <Col md="12" className="mb-3">
                                    <Label check>
                                        <Input
                                            type="checkbox"
                                            name="is_active"
                                            checked={marketData.is_active}
                                            onChange={handleMarketDataChange}
                                        />{' '}
                                        Active
                                    </Label>
                                </Col>
                            </Row>
                            <Button color="primary" type="submit" className="mt-2 search-btn-clr me-2" disabled={marketLoading}>
                                {marketLoading ? <Spinner size="sm" /> : 'Save Market Data Account'}
                            </Button>
                            <Button color="success" type="button" className="mt-2" onClick={handleMarketDataConnect} disabled={marketLoading}>
                                {marketLoading ? <Spinner size="sm" /> : 'Generate Upstox Token'}
                            </Button>
                        </Form>
                    </CardBody>
                </Card>
            </Col>
        </>
    );
};

export default WebSocket;
