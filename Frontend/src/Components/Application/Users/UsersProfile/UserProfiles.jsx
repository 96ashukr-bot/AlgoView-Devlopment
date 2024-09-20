import React, { useState, useEffect } from 'react';
import { fetchUserProfile, updateUserProfile, changePassword } from '../../../../Services/Authentication';
import { Container, Row, Col, Card, CardBody, Form, FormGroup, Label, Input, Nav, NavItem, NavLink, TabContent, TabPane, Button } from 'reactstrap';
import DatePicker from 'react-datepicker';
import { Eye, EyeOff, Target, Info, CheckCircle } from 'react-feather';
import 'react-datepicker/dist/react-datepicker.css';

const UserProfiles = () => {
  const [startDate, setStartDate] = useState(new Date());
  const [endDate, setEndDate] = useState(null);
  const [activeTab, setActiveTab] = useState('1');

  // State to store user profile data
  const [userProfile, setUserProfile] = useState({
    email: '',
    firstName: '',
    lastName: '',
    fullName: '',
    phoneNumber: '',
    PANEL_CLIENT_KEY: '',
    start_date: null,
    end_date: null,
    client_type: ''
  });

  // States for handling password change
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [showOldPassword, setShowOldPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Fetch user profile from API
  useEffect(() => {
    const getUserProfile = async () => {
      try {
        const data = await fetchUserProfile();
        setUserProfile(data);
        setStartDate(new Date(data.start_date));
        setEndDate(data.end_date ? new Date(data.end_date) : null);
      } catch (error) {
        console.error("Error fetching user profile:", error);
      }
    };

    getUserProfile();
  }, []);

  // Function to toggle password visibility
  const togglePasswordVisibility = (passwordType) => {
    if (passwordType === 'old') {
      setShowOldPassword(!showOldPassword);
    } else if (passwordType === 'new') {
      setShowNewPassword(!showNewPassword);
    } else if (passwordType === 'confirm') {
      setShowConfirmPassword(!showConfirmPassword);
    }
  };

  // Function to handle password change
  const handlePasswordChange = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      alert("New Password and Confirm Password do not match!");
      return;
    }
    try {
      await changePassword(oldPassword, newPassword, confirmPassword);
      alert("Password changed successfully!");
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      alert(error.message);
    }
  };

  // Function to update user profile
  const handleUserProfileUpdate = async (e) => {
    e.preventDefault();
    try {
      const updatedProfile = {
        ...userProfile,
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate ? endDate.toISOString().split('T')[0] : null
      };
      await updateUserProfile(updatedProfile);
      alert("Profile updated successfully!");
    } catch (error) {
      alert("Error updating profile: " + error.message);
    }
  };


  return (
    <Container fluid>
      <Row className="justify-content-center">
        <Col md="10" style={{ width: '100%' }}>
          <Card>
            <CardBody>
              <Row style={{ minHeight: '400px' }}>
                {/* Left Section: Profile Picture */}
                <Col md="4" className="border-right">
                  <div className="text-center">
                    <h5 style={{ marginTop: '16px', marginBottom: '50px' }}>User Profile</h5>
                    <img
                      src="https://via.placeholder.com/150"
                      alt="User Profile"
                      className="img-fluid rounded-circle mb-3"
                    />
                  </div>
                </Col>

                {/* Right Section: Tabs and Forms */}
                <Col md="8" style={{ width: '50%', cursor: 'pointer' }}>
                  <Nav tabs className="border-tab">
                    <NavItem>
                      <NavLink
                        className={activeTab === '1' ? 'active' : ''}
                        onClick={() => setActiveTab('1')}
                      >
                        <Target /> About Me
                      </NavLink>
                    </NavItem>
                    <NavItem>
                      <NavLink
                        className={activeTab === '2' ? 'active' : ''}
                        onClick={() => setActiveTab('2')}
                      >
                        <Info /> Change Password
                      </NavLink>
                    </NavItem>
                    <NavItem>
                      <NavLink
                        className={activeTab === '3' ? 'active' : ''}
                        onClick={() => setActiveTab('3')}
                      >
                        <CheckCircle /> Modify Updates
                      </NavLink>
                    </NavItem>
                  </Nav>

                  <TabContent activeTab={activeTab}>
                    {/* Tab 1: About Me */}
                    <TabPane tabId="1">
                      <p style={{ fontSize: '18px', fontWeight: '500' }}>Personal Information</p>
                      <Form className="theme-form" onSubmit={handleUserProfileUpdate}>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">First Name</Label>
                          <Col sm="8">
                            <Input
                              type="text"
                              value={userProfile.firstName}
                              onChange={(e) => setUserProfile({ ...userProfile, firstName: e.target.value })}
                              placeholder="First Name"
                            />
                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Last Name</Label>
                          <Col sm="8">
                            <Input
                              type="text"
                              value={userProfile.lastName}
                              onChange={(e) => setUserProfile({ ...userProfile, lastName: e.target.value })}
                              placeholder="Last Name"
                            />
                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Email</Label>
                          <Col sm="8">
                            <Input
                              type="email"
                              value={userProfile.email}
                              onChange={(e) => setUserProfile({ ...userProfile, email: e.target.value })}
                              placeholder="Email"
                            />
                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Contact Number</Label>
                          <Col sm="8">
                            <Input
                              type="text"
                              value={userProfile.phoneNumber}
                              onChange={(e) => setUserProfile({ ...userProfile, phoneNumber: e.target.value })}
                              placeholder="Contact Number"
                            />
                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Panel Client Key</Label>
                          <Col sm="8">
                            <Input
                              type="text"
                              value={userProfile.PANEL_CLIENT_KEY}
                              onChange={(e) => setUserProfile({ ...userProfile, PANEL_CLIENT_KEY: e.target.value })}
                              placeholder="Panel Client Key"
                            />
                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Start Date</Label>
                          <Col sm="8">
                            <DatePicker
                              className="form-control"
                              selected={startDate}
                              onChange={(date) => setStartDate(date)}
                            />
                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">End Date</Label>
                          <Col sm="8">
                            <DatePicker
                              className="form-control"
                              selected={endDate}
                              onChange={(date) => setEndDate(date)}
                              placeholderText="No end date"
                            />
                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Client Type</Label>
                          <Col sm="8">
                            <Input
                              type="text"
                              value={userProfile.client_type || "N/A"}
                              onChange={(e) => setUserProfile({ ...userProfile, client_type: e.target.value })}
                              placeholder="Client Type"
                            />
                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Col sm="8" className="ml-auto">
                            <button type="submit" className="btn btn-primary">Update Profile</button>
                          </Col>
                        </FormGroup>
                      </Form>
                    </TabPane>

                    {/* Tab 2: Change Password */}
                    <TabPane tabId="2">
                    <p style={{ fontSize: '18px', fontWeight: '500', fontStyle: 'bold' }}>Change Password</p>
                      <Form className="theme-form" onSubmit={handlePasswordChange}>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Old Password</Label>
                          <Col sm="8" className="position-relative">
                            <Input
                              type={showOldPassword ? 'text' : 'password'}
                              placeholder="Enter Old Password"
                              value={oldPassword}
                              onChange={(e) => setOldPassword(e.target.value)}
                            />
                            <div
                              className="position-absolute"
                              style={{ top: '28%', right: '22px', cursor: 'pointer' }}
                              onClick={() => togglePasswordVisibility('old')}  // Corrected here
                            >
                              {showOldPassword ? <EyeOff /> : <Eye />}
                            </div>
                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">New Password</Label>
                          <Col sm="8" className="position-relative">
                            <Input
                              type={showNewPassword ? 'text' : 'password'}
                              placeholder="Enter New Password"
                              value={newPassword}
                              onChange={(e) => setNewPassword(e.target.value)}
                            />
                            <div
                              className="position-absolute"
                              style={{ top: '28%', right: '22px', cursor: 'pointer' }}
                              onClick={() => togglePasswordVisibility('new')}  // Corrected here
                            >
                              {showNewPassword ? <EyeOff /> : <Eye />}
                            </div>
                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Confirm Password</Label>
                          <Col sm="8" className="position-relative">
                            <Input
                              type={showConfirmPassword ? 'text' : 'password'}
                              placeholder="Confirm New Password"
                              value={confirmPassword}
                              onChange={(e) => setConfirmPassword(e.target.value)}
                            />
                            <div
                              className="position-absolute"
                              style={{ top: '28%', right: '22px', cursor: 'pointer' }}
                              onClick={() => togglePasswordVisibility('confirm')}  // Corrected here
                            >
                              {showConfirmPassword ? <EyeOff /> : <Eye />}
                            </div>
                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Col sm="8" className="ml-auto">
                            <button type="submit" className="btn btn-primary">Update Password</button>
                          </Col>
                        </FormGroup>
                      </Form>
                    </TabPane>


                    {/* Tab 3: Modify Updates */}
                    <TabPane tabId="3">
                      <p style={{ fontSize: '18px', fontWeight: '500', fontStyle: 'bold', marginBottom: '30px' }}>Modify Updates</p>
                      <p style={{ fontSize: '18px', fontWeight: '300', fontStyle: 'bold', marginBottom: '15px' }} className="col-form-label col-sm-3 pt-0">Web Login</p>
                      <Form className="theme-form">
                        <Row>
                          <Col sm="9">
                            <div className="d-flex flex-row">
                              <div className="radio radio-primary ms-2 d-flex align-items-center">
                                <Input type="radio" name="radio1" id="radio1" value="option1" />
                                <Label for="radio1" className="ms-2">Admin</Label>
                              </div>
                              <div className="radio radio-primary ms-2 d-flex align-items-center">
                                <Input type="radio" name="radio1" id="radio2" value="option1" />
                                <Label for="radio2" className="ms-2">Individual</Label>
                              </div>
                            </div>
                          </Col>
                        </Row>
                      </Form>
                      <p style={{ fontSize: '18px', fontWeight: '300', fontStyle: 'bold', marginTop: '15px' }}>Signals Execution Type</p>
                      <Form className="theme-form">
                        <Row>
                          <Col sm="9">
                            <div className="d-flex flex-row">
                              <div className="radio radio-primary ms-2 d-flex align-items-center">
                                <Input type="radio" name="radio3" id="radio3" value="option1" />
                                <Label for="radio3" className="ms-2">App</Label>
                              </div>
                              <div className="radio radio-primary ms-2 d-flex align-items-center">
                                <Input type="radio" name="radio3" id="radio4" value="option1" />
                                <Label for="radio4" className="ms-2">Individual</Label>
                              </div>
                            </div>
                          </Col>
                        </Row>
                        <FormGroup className="row">
                          <Col sm="8" className="ml-auto">
                            <button type="submit" className="btn btn-primary">Continue</button>
                          </Col>
                        </FormGroup>
                      </Form>
                    </TabPane>
                  </TabContent>
                </Col>
              </Row>
            </CardBody>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default UserProfiles;
