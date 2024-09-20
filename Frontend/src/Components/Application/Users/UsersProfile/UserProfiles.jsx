import React, { useState } from 'react';
import { Container, Row, Col, Card, CardBody, Form, FormGroup, Label, Input, Nav, NavItem, NavLink, TabContent, TabPane } from 'reactstrap';
import { Eye, EyeOff, Target, Info, CheckCircle } from 'react-feather';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

const UserProfiles = () => {
  const [startDate, setStartDate] = useState(new Date());
  const [endDate, setEndDate] = useState(new Date());
  const [activeTab, setActiveTab] = useState('1');

  // Password state
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Toggle visibility state
  const [showOldPassword, setShowOldPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Error state
  const [errors, setErrors] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  const handlePasswordChange = (e) => {
    e.preventDefault();
    const newErrors = {
      oldPassword: '',
      newPassword: '',
      confirmPassword: '',
    };

    if (oldPassword.length < 8) newErrors.oldPassword = 'Password must be at least 8 characters long.';
    if (newPassword.length < 8) newErrors.newPassword = 'Must contain at least 8 characters.';
    if (newPassword !== confirmPassword) newErrors.confirmPassword = 'New passwords do not match.';

    setErrors(newErrors);
  };

  // Function to toggle password visibility
  const togglePasswordVisibility = (setter) => {
    setter((prevState) => !prevState);
  };

  return (
    <Container fluid>
      <Row className="justify-content-center">
        {/* Single Card containing both Profile and Tabs */}
        <Col md="10" style={{ width: '100%' }}>
          <Card>
            <CardBody>
              <Row style={{ minHeight: '400px' }}>
                {/* Left Section: Profile Details */}
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
                      <p style={{ fontSize: '18px', fontWeight: '500', fontStyle: 'bold' }}>Personal Information</p>
                      <Form className="theme-form">
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Name</Label>
                          <Col sm="8">
                            <Input type="text" placeholder="Enter Your Name" />
                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Email</Label>
                          <Col sm="8">
                            <Input type="email" placeholder="Enter Your Email" />
                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Contact Number</Label>
                          <Col sm="8">
                            <Input type="number" placeholder="Enter Contact Number" />
                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Panel Client Key</Label>
                          <Col sm="8">
                            <Input type="text" placeholder="Enter Panel Client Key" />
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
                            />
                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Client Type</Label>
                          <Col sm="8">
                            <Input type="text" placeholder="Enter Client Type" />
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
                              onClick={() => togglePasswordVisibility(setShowOldPassword)}
                            >
                              {showOldPassword ? <EyeOff /> : <Eye />}
                            </div>
                            {errors.oldPassword && <small className="text-danger">{errors.oldPassword}</small>}
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
                              onClick={() => togglePasswordVisibility(setShowNewPassword)}
                            >
                              {showNewPassword ? <EyeOff /> : <Eye />}
                            </div>
                            {errors.newPassword && <small className="text-danger">{errors.newPassword}</small>}
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
                              onClick={() => togglePasswordVisibility(setShowConfirmPassword)}
                            >
                              {showConfirmPassword ? <EyeOff /> : <Eye />}
                            </div>
                            {errors.confirmPassword && <small className="text-danger">{errors.confirmPassword}</small>}
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
