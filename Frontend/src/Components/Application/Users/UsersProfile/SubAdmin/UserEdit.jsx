import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom'; 
import { ToastContainer, toast } from 'react-toastify';
import { fetchRolesList, updateUser, fetchUserById } from '../../../../../Services/Authentication';
import 'react-toastify/dist/ReactToastify.css';
import { Col, Card, CardHeader, CardBody, Form, Label, Row, Input, Button,Spinner } from 'reactstrap';
import './UserEdit.css'; 

const EditUser = () => {
  const { id } = useParams();
  const navigate = useNavigate(); 
  const [userDetails, setUserDetails] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phoneNumber: '',
    role: ''
  });
  const [loading, setLoading] = useState(true);
  const [originalEmail, setOriginalEmail] = useState('');
  const [roleOptions, setRoleOptions] = useState([]);
  const [errors, setErrors] = useState({}); 

  useEffect(() => {
    const getUserDetails = async () => {
      try {
        const userData = await fetchUserById(id);
        
        setUserDetails({
          firstName: userData.firstName || '',
          lastName: userData.lastName || '',
          email: userData.email || '',
          phoneNumber: userData.phoneNumber || '',
          role: userData.role ? userData.role.id : '' 
        });
        setOriginalEmail(userData.email || '');
      } catch (error) {
        console.error("Error fetching user data:", error);
      }
    };
  
    const getRolesList = async () => {
      try {
        const roles = await fetchRolesList(); 
        setRoleOptions(roles); 
      } catch (error) {
        console.error("Error fetching roles:", error);
      }
    };
  
    getUserDetails();
    getRolesList();
    
    setLoading(false);
  }, [id]);
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setUserDetails({ ...userDetails, [name]: value });
  };

  const validate = () => {
    const newErrors = {};
    
    console.log(userDetails); 

    if (!userDetails.firstName) newErrors.firstName = 'First name is required.';
    if (!userDetails.lastName) newErrors.lastName = 'Last name is required.';
    if (!userDetails.email) {
        newErrors.email = 'Email is required.';
    } else if (!/\S+@\S+\.\S+/.test(userDetails.email)) {
        newErrors.email = 'Email format is invalid.';
    }
    if (!userDetails.phoneNumber) {
        newErrors.phoneNumber = 'Phone number is required.';
    } else if (!/^\d{10}$/.test(userDetails.phoneNumber)) { 
        newErrors.phoneNumber = 'Phone number must be a 10-digit number.';
    }
    if (!userDetails.role) newErrors.role = 'Role is required.';
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0; 
};


  const handleSubmit = async (e) => {
    e.preventDefault(); 
    const isValid = validate(); 

    if (!isValid) {
        return;
    }

    const updatedUserDetails = { ...userDetails };
    if (userDetails.email === originalEmail) {
        delete updatedUserDetails.email; 
    }

    try {
        await updateUser(id, updatedUserDetails); 
        toast.success('User updated successfully!');
        setTimeout(() => {
            navigate('/subadmin/userlist'); 
        }, 3000);
    } catch (error) {
        console.error("Error updating user:", error);
        toast.error(error.response?.data?.message || 'Error updating user.'); 
    }
};


  const handleCancel = () => {
    navigate(`/subadmin/userlist`); 
  };

  if (loading) {
    return <div>Loading user details...</div>;
  }

  return (
    <div>
      <ToastContainer />
      <Card className="mt-5">
        <CardHeader>
          <h5>Edit User</h5>
          {/* <span>
            Use the form below to edit user details. Ensure to provide valid information for each field. Click submit once done.
          </span> */}
        </CardHeader>
        <CardBody>
          <Form className="needs-validation" onSubmit={handleSubmit}>
            <Row>
              {/* First Name Field */}
              <Col md="6 mb-3">
                <Label htmlFor="firstName">First Name
                  <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                </Label>
                <Input
                  type="text"
                  name="firstName"
                  className='custom-input-style'
                  value={userDetails.firstName}
                  onChange={handleChange}
                  placeholder="Enter First Name"
                  required
                  invalid={!!errors.firstName}
                />
                {errors.firstName && <div className="invalid-feedback text-danger">{errors.firstName}</div>}
              </Col>

              {/* Last Name Field */}
              <Col md="6 mb-3">
                <Label htmlFor="lastName">Last Name
                  <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                </Label>
                <Input
                  type="text"
                  name="lastName"
                  className='custom-input-style'
                  value={userDetails.lastName}
                  onChange={handleChange}
                  placeholder="Enter Last Name"
                  required
                  invalid={!!errors.lastName}
                />
                {errors.lastName && <div className="invalid-feedback text-danger">{errors.lastName}</div>}
              </Col>

              {/* Email Field */}
              <Col md="6 mb-3">
                <Label htmlFor="email">Email
                  <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                </Label>
                <Input
                  type="email"
                  name="email"
                  className='custom-input-style'
                  value={userDetails.email}
                  onChange={handleChange}
                  placeholder="Enter Email"
                  required
                  invalid={!!errors.email}
                />
                {errors.email && <div className="invalid-feedback text-danger">{errors.email}</div>}
              </Col>

              {/* Phone Number Field */}
              <Col md="6 mb-3">
                <Label htmlFor="phoneNumber">Phone Number
                  <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                </Label>
                <Input
                  type="text"
                  name="phoneNumber"
                  className='custom-input-style'
                  value={userDetails.phoneNumber}
                  onChange={handleChange}
                  placeholder="Enter Phone Number"
                  required
                  invalid={!!errors.phoneNumber}
                />
                {errors.phoneNumber && <div className="invalid-feedback text-danger">{errors.phoneNumber}</div>}
              </Col>

              {/* Role Field */}
              <Col md="6 mb-3">
                <Label htmlFor="role">Role
                  <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                </Label>
                <Input
                  type="select"
                  name="role"
                  className='custom-input-style'
                  value={userDetails.role}
                  onChange={handleChange}
                  required
                  invalid={!!errors.role}
                >
                  <option value="">Select Role</option>
                  {roleOptions.map(role => (
                    <option key={role.id} value={role.id}>{role.name}</option>
                  ))}
                </Input>
                {errors.role && <div className="invalid-feedback text-danger">{errors.role}</div>}
              </Col>
            </Row>

            <Button type="submit" color="primary" className=" btn btn-primary search-btn-clr mt-4" disabled={loading}> 
            {loading ? <Spinner size="sm" /> : 'Update User'}
            </Button>
            <Button type="button" color="danger" className="mt-4 ml-2" onClick={handleCancel} style={{marginLeft:'10px'}}>Cancel</Button>
          </Form>
        </CardBody>
      </Card>
    </div>
  );
};

export default EditUser;
