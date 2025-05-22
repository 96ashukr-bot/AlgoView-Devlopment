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
import { updateWebSocket, getWebsocket } from '../../../../Services/Authentication';

const WebSocket = () => {
    const [socketDetails, setSocketDetails] = useState({
        auth_token: '',
        token_status: '',
        status: '',
    });

    const [errors, setErrors] = useState({});
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchSocketDetails();
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
        </>
    );
};

export default WebSocket;
