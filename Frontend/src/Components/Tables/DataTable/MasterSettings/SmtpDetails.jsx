import React, { useState, useEffect } from 'react';
import { Col, Card, CardHeader, CardBody, Form, Label, Row, Input, Button, Spinner } from 'reactstrap';
import { ToastContainer, toast } from 'react-toastify';
import Swal from 'sweetalert2';
import 'react-toastify/dist/ReactToastify.css';
import { updateSmtpDetails, getSmtpDetails } from '../../../../Services/Authentication';

const SmtpDetails = () => {
  const [SmtpDetails, setSmtpDetails] = useState({
    email_host: '',
    email_port: '',
    email_host_user: '',
    email_host_password: '',
    default_from_email: '',
  });

  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchSmtpDetails();
  }, []);

  const fetchSmtpDetails = async () => {
    try {
      const response = await getSmtpDetails();
      if (response.status === 'success' && response.data) {
        setSmtpDetails({
          email_host: response.data.email_host || '',
          email_port: response.data.email_port || '',
          email_host_user: response.data.email_host_user || '',
          email_host_password: response.data.email_host_password || '',
          default_from_email: response.data.default_from_email || '',
        });

      } else {
        console.error(response.message || 'Failed to fetch company details');
      }
    } catch (error) {
      toast.error(error.message || 'Something went wrong');
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSmtpDetails((prevData) => ({
      ...prevData,
      [name]: type === "checkbox" ? checked : value,
    }));
    setErrors((prevErrors) => ({ ...prevErrors, [name]: '' }));
  };

  const validateForm = () => {
    const newErrors = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!SmtpDetails.email_host) newErrors.email_host = 'Email Host is required';
    
    if (!SmtpDetails.email_host) newErrors.email_host = 'Invalid Email Host format';

    if (!SmtpDetails.email_host_user) newErrors.email_host_user = 'Email Host User is required';
    else if (!emailRegex.test(SmtpDetails.email_host_user)) newErrors.email_host_user = 'Invalid Email Host User format';

    if (!SmtpDetails.default_from_email) newErrors.default_from_email = 'Default Email is required';
    else if (!emailRegex.test(SmtpDetails.default_from_email)) newErrors.default_from_email = 'Invalid Default Email format';

    // Port and Password validation
    if (!SmtpDetails.email_port) newErrors.email_port = 'Port is required';
    if (!SmtpDetails.email_host_password) newErrors.email_host_password = 'Password is required';

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

    setLoading(true);
    try {
      const response = await updateSmtpDetails(SmtpDetails);
      if (response.status === 'success') {
        toast.success(response.message || 'SMTP Details updated successfully!');
      } else {
        toast.error(response.message || 'Failed to update SMTP details');
      }
    } catch (error) {
      toast.error(error.message || 'An error occurred while updating SMTP details');
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
            <h5>Update SMTP Details</h5>
          </CardHeader>
          <CardBody>
            <Form className="needs-validation mt-3" noValidate onSubmit={handleSubmit}>
              <Row>
                <Col md="4 mb-3">
                  <Label htmlFor="email_host">Email Host
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="text"
                    className={`form-control ${errors.email_host ? 'is-invalid' : ''} custom-input-style`}
                    name="email_host"
                    id="email_host"
                    placeholder="Enter Host Email"
                    value={SmtpDetails.email_host}
                    onChange={handleChange}
                    required
                  />
                  {errors.email_host && <div className="invalid-feedback text-danger">{errors.email_host}</div>}
                </Col>

                <Col md="4 mb-3">
                  <Label htmlFor="email_host_password">Email Host Password
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="text"
                    className={`form-control ${errors.email_host_password ? 'is-invalid' : ''} custom-input-style custom-input-style`}
                    name="email_host_password"
                    id="email_host_password"
                    placeholder="Enter Email Host Password"
                    value={SmtpDetails.email_host_password}
                    onChange={handleChange}
                    required
                  />
                  {errors.email_host_password && <div className="invalid-feedback text-danger">{errors.email_host_password}</div>}
                </Col>

                <Col md="4 mb-3">
                  <Label htmlFor="email_host_user">
                    Email Host User<span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="email_host_user"
                    className={`form-control ${errors.email_host_user ? 'is-invalid' : ''} custom-input-style`}
                    name="email_host_user"
                    id="email_host_user"
                    placeholder="Enter Email Host User"
                    value={SmtpDetails.email_host_user}
                    onChange={handleChange}
                    required
                  />
                  {errors.email_host_user && <div className="invalid-feedback text-danger">{errors.email_host_user}</div>}
                </Col>

                <Col md="4 mb-3">
                  <Label htmlFor="email_port">Email Port
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="text"
                    className={`form-control ${errors.email_port ? 'is-invalid' : ''} custom-input-style`}
                    name="email_port"
                    id="email_port"
                    placeholder="Enter Email Port"
                    value={SmtpDetails.email_port}
                    onChange={handleChange}
                    required
                  />
                  {errors.email_port && <div className="invalid-feedback text-danger">{errors.email_port}</div>}
                </Col>

                <Col md="4 mb-3">
                  <Label htmlFor="default_from_email">Default Email
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="text"
                    className={`form-control ${errors.default_from_email ? 'is-invalid' : ''} custom-input-style`}
                    name="default_from_email"
                    id="default_from_email"
                    placeholder="Enter Email Host User"
                    value={SmtpDetails.default_from_email}
                    onChange={handleChange}
                    required
                  >
                  </Input>
                  {errors.default_from_email && <div className="invalid-feedback text-danger">{errors.default_from_email}</div>}
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

export default SmtpDetails;
