import React, { useState, useEffect } from 'react';
import { Col, Card, CardHeader, CardBody, Form, Label, Row, Input, Button, Spinner } from 'reactstrap';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import Swal from 'sweetalert2';
import { baseUrl } from '../../../../ConfigUrl/config';
import { AiOutlineCloseCircle } from 'react-icons/ai';
import { updateCompanyDetails, getCompanyDetails } from '../../../../Services/Authentication';

const CompanyDetails = () => {
    const [formData, setFormData] = useState({
        companyName: '',
        companyEmail: '',
        supportEmail: '',
        phoneNumber: '',
        senderName: '',
        companyLogo: null,
        companyFavicon: null,
        loginLink: '',
        helpCenterLink: '',
        companyWebsite: ''
    });

    const [previewLogo, setPreviewLogo] = useState(null);
    const [previewFavicon, setPreviewFavicon] = useState(null);
    const [errors, setErrors] = useState({});
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchCompanyDetails();
        const storedFavicon = localStorage.getItem('companyFavicon');
        if (storedFavicon) {
            setPreviewFavicon(storedFavicon);
            updateFavicon(storedFavicon);
        }

    }, []);

    const fetchCompanyDetails = async () => {
        try {
            const response = await getCompanyDetails();
            if (response.status === 'success' && response.data) {
                setFormData({
                    companyName: response.data.company_name || '',
                    companyEmail: response.data.company_email || '',
                    supportEmail: response.data.company_support_email || '',
                    phoneNumber: response.data.company_phone_number || '',
                    senderName: response.data.company_sender_name || '',
                    companyLogo: null,
                    companyFavicon: null,
                    loginLink: response.data.login_link || '',
                    helpCenterLink: response.data.help_center_link || '',
                    companyWebsite: response.data.company_website || ''
                });

                if (response.data.company_logo) {
                    const logoUrl = `${baseUrl}${response.data.company_logo}`;
                    setPreviewLogo(logoUrl);
                }

                if (response.data.company_favicon) {
                    const faviconUrl = `${baseUrl}${response.data.company_favicon}`;
                    setPreviewFavicon(faviconUrl);
                    localStorage.setItem('companyFavicon', faviconUrl); // Store favicon URL in local storage
                    updateFavicon(faviconUrl);
                }
                if (response.data.company_favicon) {
                    setPreviewFavicon(`${baseUrl}${response.data.company_favicon}`);
                }
            } else {
                console.error(response.message || 'Failed to fetch company details');
            }
        } catch (error) {
            toast.error(error.message || 'Something went wrong');
        }
    };

    const handleChange = (e) => {
        const { name, type, files, value } = e.target;
        if (type === 'file') {
            const file = files[0];
            if (file) {
                setFormData((prevData) => ({ ...prevData, [name]: file }));
                if (name === 'companyLogo') {
                    setPreviewLogo(URL.createObjectURL(file));
                } else if (name === 'companyFavicon') {
                    setPreviewFavicon(URL.createObjectURL(file)); // Only update preview, not the actual favicon
                }
            }
        } else {
            setFormData((prevData) => ({ ...prevData, [name]: value }));
        }
        setErrors((prevErrors) => ({ ...prevErrors, [name]: '' }));
    };

    const removeImage = () => {
        setFormData((prevData) => ({ ...prevData, companyLogo: null, companyFavicon: null }));
        setPreviewLogo(null);
    };

    const removeFavicon = () => {
        setFormData((prevData) => ({ ...prevData, companyFavicon: null }));
        setPreviewFavicon(null);
        localStorage.removeItem('companyFavicon'); // Remove favicon URL from local storage
        updateFavicon(null); // Optionally, set a default favicon or remove it
    };

    const validateForm = () => {
        const newErrors = {};
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const phoneRegex = /^[0-9]{10}$/;

        if (!formData.companyName) newErrors.companyName = 'Company Name is required';
        if (!formData.companyEmail || !emailRegex.test(formData.companyEmail)) newErrors.companyEmail = 'Valid Company Email is required';
        if (!formData.supportEmail || !emailRegex.test(formData.supportEmail)) newErrors.supportEmail = 'Valid Support Email is required';
        if (!formData.phoneNumber || !phoneRegex.test(formData.phoneNumber)) newErrors.phoneNumber = 'Valid 10-digit Phone Number is required';
        if (!formData.senderName) newErrors.senderName = 'Sender Name is required';
        if (!formData.loginLink) newErrors.loginLink = 'Login Link is required';
        if (!formData.helpCenterLink) newErrors.helpCenterLink = 'Help Center Link is required';
        if (!formData.companyWebsite) newErrors.companyWebsite = 'Company Website is required';

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

        const payload = {
            company_name: formData.companyName,
            company_email: formData.companyEmail,
            company_support_email: formData.supportEmail,
            company_phone_number: parseInt(formData.phoneNumber),
            company_sender_name: formData.senderName,
            company_logo: formData.companyLogo || {},
            company_favicon: formData.companyFavicon || {},
            login_link: formData.loginLink,
            help_center_link: formData.helpCenterLink,
            company_website: formData.companyWebsite
        };

        setLoading(true);

        try {
            const response = await updateCompanyDetails(payload);
            if (response.status === 'success') {
                toast.success(response.message);

                if (formData.companyLogo) {
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        const logoUrl = e.target.result;
                        localStorage.setItem('companyLogo', logoUrl);
                    };
                    reader.readAsDataURL(formData.companyLogo);
                }

                // Update favicon only after successful save
                if (formData.companyFavicon) {
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        const faviconUrl = e.target.result;
                        localStorage.setItem('companyFavicon', faviconUrl); // Store favicon URL in local storage
                        updateFavicon(faviconUrl); // Update favicon in the DOM
                    };
                    reader.readAsDataURL(formData.companyFavicon);
                }
            } else {
                toast.error(response.message || 'Error updating company details');
            }
        } catch (error) {
            console.error(error.message || 'Something went wrong');
        } finally {
            setLoading(false);
        }
    };

    const updateFavicon = (faviconUrl) => {
        // Remove all favicon links first
        const existingFavicons = document.querySelectorAll("link[rel~='icon']");
        existingFavicons.forEach(link => link.parentNode.removeChild(link));

        if (faviconUrl) {
            const newLink = document.createElement('link');
            newLink.rel = 'icon';
            newLink.href = faviconUrl;
            document.head.appendChild(newLink);
        }
    };

    return (
        <>
            <ToastContainer />
            <Col sm="12">
                <Card className="mt-5">
                    <CardHeader>
                        <h5>Update Company Details</h5>
                    </CardHeader>
                    <CardBody>
                        <Form className="needs-validation mt-3" noValidate onSubmit={handleSubmit}>
                            <Row>
                                <Col md="6" className="mb-3">
                                    <Label htmlFor="companyName">Company Name
                                        <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                                    </Label>
                                    <Input
                                        type="text"
                                        className={`form-control ${errors.companyName ? 'is-invalid' : ''} custom-input-style`}
                                        name="companyName"
                                        id="companyName"
                                        placeholder="Enter Company Name"
                                        value={formData.companyName}
                                        onChange={handleChange}
                                        required
                                    />
                                    {errors.companyName && <div className="invalid-feedback text-danger">{errors.companyName}</div>}
                                </Col>

                                <Col md="6" className="mb-3">
                                    <Label htmlFor="companyEmail">Company Email
                                        <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                                    </Label>
                                    <Input
                                        type="text"
                                        className={`form-control ${errors.companyEmail ? 'is-invalid' : ''} custom-input-style custom-input-style`}
                                        name="companyEmail"
                                        id="companyEmail"
                                        placeholder="Enter Company Email"
                                        value={formData.companyEmail}
                                        onChange={handleChange}
                                        required
                                    />
                                    {errors.companyEmail && <div className="invalid-feedback text-danger">{errors.companyEmail}</div>}
                                </Col>

                                <Col md="6" className="mb-3">
                                    <Label htmlFor="supportEmail">
                                        Support Email <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                                    </Label>
                                    <Input
                                        type="supportEmail"
                                        className={`form-control ${errors.supportEmail ? 'is-invalid' : ''} custom-input-style`}
                                        name="supportEmail"
                                        id="supportEmail"
                                        placeholder="Enter Support Email"
                                        value={formData.supportEmail}
                                        onChange={handleChange}
                                        required
                                    />
                                    {errors.supportEmail && <div className="invalid-feedback text-danger">{errors.supportEmail}</div>}
                                </Col>

                                <Col md="6" className="mb-3">
                                    <Label htmlFor="phoneNumber">Phone Number
                                        <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                                    </Label>
                                    <Input
                                        type="text"
                                        className={`form-control ${errors.phoneNumber ? 'is-invalid' : ''} custom-input-style`}
                                        name="phoneNumber"
                                        id="phoneNumber"
                                        placeholder="Enter Phone Number"
                                        value={formData.phoneNumber}
                                        onChange={handleChange}
                                        required
                                    />
                                    {errors.phoneNumber && <div className="invalid-feedback text-danger">{errors.phoneNumber}</div>}
                                </Col>

                                <Col md="6" className="mb-3">
                                    <Label htmlFor="senderName">Sender Name
                                        <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                                    </Label>
                                    <Input
                                        type="text"
                                        className={`form-control ${errors.senderName ? 'is-invalid' : ''} custom-input-style`}
                                        name="senderName"
                                        id="senderName"
                                        placeholder="Enter Sender Name"
                                        value={formData.senderName}
                                        onChange={handleChange}
                                        required
                                    />
                                    {errors.senderName && <div className="invalid-feedback text-danger">{errors.senderName}</div>}
                                </Col>

                                <Col md="6" className="mb-3">
                                    <Label htmlFor="companyLogo">Comapny Logo
                                        <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                                    </Label>
                                    <Input
                                        type="file"
                                        name="companyLogo"
                                        id="companyLogo"
                                        onChange={handleChange}
                                        className="form-control custom-input-style"
                                    />
                                    {previewLogo && (
                                        <div className="mt-3 position-relative">
                                            <img
                                                src={previewLogo}
                                                alt="Logo Preview"
                                                style={{ maxWidth: '200px', borderRadius: '8px' }}
                                            />
                                            <AiOutlineCloseCircle
                                                size={24}
                                                className="position-absolute top-0 end-0 text-danger cursor-pointer"
                                                onClick={() => removeImage('companyLogo')}
                                            />
                                        </div>
                                    )}
                                </Col>
                                <Col md="6" className="mb-3">
                                    <Label htmlFor="companyFavicon">Comapny Favicon
                                        <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                                    </Label>
                                    <Input
                                        type="file"
                                        name="companyFavicon"
                                        id="companyFavicon"
                                        onChange={handleChange}
                                        className="form-control custom-input-style"
                                    />
                                    {previewFavicon && (
                                        <div className="mt-3 position-relative">
                                            <img
                                                src={previewFavicon}
                                                alt="Favicon Preview"
                                                style={{ maxWidth: '200px', borderRadius: '8px' }}
                                            />
                                            <AiOutlineCloseCircle
                                                size={24}
                                                className="position-absolute top-0 end-0 text-danger cursor-pointer"
                                                onClick={() => removeFavicon('companyFavicon')}
                                            />
                                        </div>
                                    )}
                                </Col>
                                <Col md="6" className="mb-3">
                                    <Label htmlFor="loginLink">Login Link
                                        <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                                    </Label>
                                    <Input
                                        type="text"
                                        className={`form-control ${errors.loginLink ? 'is-invalid' : ''}`}
                                        name="loginLink"
                                        id="loginLink"
                                        placeholder="Enter Login Link"
                                        value={formData.loginLink}
                                        onChange={handleChange}
                                        required
                                    />
                                    {errors.loginLink && <div className="invalid-feedback text-danger">{errors.loginLink}</div>}
                                </Col>

                                <Col md="6" className="mb-3">
                                    <Label htmlFor="helpCenterLink">Help Center Link
                                        <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                                    </Label>
                                    <Input
                                        type="text"
                                        className={`form-control ${errors.helpCenterLink ? 'is-invalid' : ''}`}
                                        name="helpCenterLink"
                                        id="helpCenterLink"
                                        placeholder="Enter Help Center Link"
                                        value={formData.helpCenterLink}
                                        onChange={handleChange}
                                        required
                                    />
                                    {errors.helpCenterLink && <div className="invalid-feedback text-danger">{errors.helpCenterLink}</div>}
                                </Col>

                                <Col md="6" className="mb-3">
                                    <Label htmlFor="companyWebsite">Company Website
                                        <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                                    </Label>
                                    <Input
                                        type="text"
                                        className={`form-control ${errors.companyWebsite ? 'is-invalid' : ''}`}
                                        name="companyWebsite"
                                        id="companyWebsite"
                                        placeholder="Enter Company Website"
                                        value={formData.companyWebsite}
                                        onChange={handleChange}
                                        required
                                    />
                                    {errors.companyWebsite && <div className="invalid-feedback text-danger">{errors.companyWebsite}</div>}
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

export default CompanyDetails;