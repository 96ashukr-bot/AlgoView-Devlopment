import React, { useState, useEffect } from 'react';
import { Col, Card, CardHeader, CardBody, Form, Label, Row, Input, Button, Spinner } from 'reactstrap';
import { useNavigate } from 'react-router-dom';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './UserEdit.css';
import './UserList.css';
import { addUser, fetchRolesList } from '../../../../../Services/Authentication';

const AddUser = () => {
  const [formData, setFormData] = useState({
    email: '',
    firstName: '',
    lastName: '',
    phoneNumber: '',
    role: '',
  });

  const [roleOptions, setRoleOptions] = useState([]);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [roleLoading, setRoleLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadRoles();
  }, []);

  const loadRoles = async () => {
    try {
      const roles = await fetchRolesList();
      setRoleOptions(roles);
    } catch {
      // Error handling is already in fetchRolesList, no need to re-handle here
    } finally {
      setRoleLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
    setErrors((prevErrors) => ({ ...prevErrors, [name]: '' }));
  };

  const validateForm = () => {
    const newErrors = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const mobileRegex = /^[0-9]{10}$/;

    if (!formData.firstName) newErrors.firstName = 'First Name is required';
    if (!formData.lastName) newErrors.lastName = 'Last Name is required';
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!emailRegex.test(formData.email)) {
      newErrors.email = 'Format of email is incorrect';
    }
    if (!formData.phoneNumber) {
      newErrors.phoneNumber = 'Mobile number is required';
    } else if (!mobileRegex.test(formData.phoneNumber)) {
      newErrors.phoneNumber = 'Number must be 10 digits only';
    }

    if (!formData.role) newErrors.role = 'Role is required';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };


  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
  
    setLoading(true);
  
    try {
      await addUser(formData);
      toast.success('User created successfully!');
      setTimeout(() => {
        navigate('/subadmin/userlist');
      }, 3000);
    } catch (error) {
      console.error('Error:', error.message);
  
      // Show the error in the email input field if it is email-specific
      if (error.message === "user with this email already exists.") {
        setErrors((prevErrors) => ({
          ...prevErrors,
          email: error.message,
        }));
      }else if (error.message === "A user with this phone number already exists.") {
        setErrors((prevErrors) => ({
          ...prevErrors,
          phoneNumber: error.message, // Display phone number error
        }));
      }else {
        toast.error(error.message);
      }
    } finally {
      setLoading(false);
    }
  };
  
  
  const handleCancel = () => {
    navigate('/subadmin/userlist');
  };

  return (
    <>
      <ToastContainer />
      <Col sm="12">
        <Card className="mt-5">
          <CardHeader>
            <h5>Add User</h5>
            {/* <span>
              Use the form below to add a new user. Ensure to provide valid information for each field. Click submit once done.
            </span> */}
          </CardHeader>
          <CardBody>
            <Form className="needs-validation mt-3" noValidate onSubmit={handleSubmit}>
              <Row>
                <Col md="4 mb-3">
                  <Label htmlFor="firstName">First Name
                  <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="text"
                    className={`form-control ${errors.firstName ? 'is-invalid' : ''} custom-input-style`}
                    name="firstName"
                    id="firstName"
                    placeholder="Enter First Name"
                    value={formData.firstName}
                    onChange={handleChange}
                    required
                  />
                  {errors.firstName && <div className="invalid-feedback text-danger">{errors.firstName}</div>}
                </Col>

                <Col md="4 mb-3">
                  <Label htmlFor="lastName">Last Name
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="text"
                    className={`form-control ${errors.lastName ? 'is-invalid' : ''} custom-input-style custom-input-style`}
                    name="lastName"
                    id="lastName"
                    placeholder="Enter Last Name"
                    value={formData.lastName}
                    onChange={handleChange}
                    required
                  />
                  {errors.lastName && <div className="invalid-feedback text-danger">{errors.lastName}</div>}
                </Col>

                <Col md="4 mb-3">
                  <Label htmlFor="email">
                    Email <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="email"
                    className={`form-control ${errors.email ? 'is-invalid' : ''} custom-input-style`}
                    name="email"
                    id="email"
                    placeholder="Enter Email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                  />
                  {errors.email && <div className="invalid-feedback text-danger">{errors.email}</div>}
                </Col>

                <Col md="4 mb-3">
                  <Label htmlFor="phoneNumber">Phone Number
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="text"
                    className={`form-control ${errors.phoneNumber ? 'is-invalid' : ''} custom-input-style`}
                    name="phoneNumber"
                    id="phoneNumber"
                    placeholder="Enter Phone No."
                    value={formData.phoneNumber}
                    onChange={handleChange}
                    required
                  />
                  {errors.phoneNumber && <div className="invalid-feedback text-danger">{errors.phoneNumber}</div>}
                </Col>

                <Col md="4 mb-3">
                  <Label htmlFor="role">Role
                    <span style={{ color: 'red', fontSize: '20px'}}>*</span>
                  </Label>
                  <Input
                    type="select"
                    className={`form-control ${errors.role ? 'is-invalid' : ''} custom-input-style`}
                    name="role"
                    id="role"
                    value={formData.role}
                    onChange={handleChange}
                    required
                  >
                    <option value="">Select Role</option>
                    {roleLoading ? (
                      <option>Loading roles...</option>
                    ) : (
                      roleOptions.map((role) => (
                        <option key={role.id} value={role.id}>
                          {role.name}
                        </option>
                      ))
                    )}
                  </Input>
                  {errors.role && <div className="invalid-feedback text-danger">{errors.role}</div>}
                </Col>
              </Row>

              <Button color="primary" type="submit" className="mt-4 search-btn-clr" disabled={loading}>
                {loading ? <Spinner size="sm" /> : 'Save'}
              </Button>
              <Button color="danger" type="button" className="mt-4 ml-2" style={{ marginLeft: '10px' }} onClick={handleCancel}>
                Cancel
              </Button>
            </Form>
          </CardBody>
        </Card>
      </Col>
    </>
  );
};

export default AddUser;
