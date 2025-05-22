import React, { useState, useEffect } from 'react';
import {
  fetchUserProfile, updateUserProfile, fetchClientLoginActivity, updateAddress, updateUserProfileImage, changePassword,
  fetchLastLogin, getCityData, getStateData, searchCity, searchState, getClientBrokerLoginActivity
} from '../../../../Services/Authentication';
import {
  Dropdown,
  DropdownToggle,
  DropdownMenu,
  DropdownItem, Container, Row, Col, Card, CardBody, Form, FormGroup, Label, Input, Nav, NavItem, NavLink, TabContent, TabPane, Button
} from 'reactstrap';
import man from "../../../../assets/images/dashboard/defaultpicture.jpg";
import 'react-datepicker/dist/react-datepicker.css';
import { Eye, EyeOff, Target, Info, CheckCircle, User } from 'react-feather';
import { toast, ToastContainer } from 'react-toastify';
import DatePicker from 'react-datepicker';
import 'react-toastify/dist/ReactToastify.css';
import { baseUrl } from '../../../../ConfigUrl/config';
import "./UserProfiles.css";
const UserProfiles = () => {
  const [activeTab, setActiveTab] = useState('1');
  const [sameAddress, setSameAddress] = useState(false);
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [cities, setCities] = useState([]);
  const [states, setStates] = useState([]);
  const [lastLogin, setLastLogin] = useState('');
  const [lastIP, setLastIP] = useState('');
  const [userProfileNew, setUserProfileNew] = useState([])
  const [userProfile, setUserProfile] = useState({
    email: '',
    fullName: '',
    PANEL_CLIENT_KEY: '',
    start_date: null,
    end_date: null,
    client_type: '',
    address_line1: '',
    address_line2: '',
    Country: '',
    state: '',
    city: '',
    pstate: '',
    pcity: '',
    zip_code: '',
  });
  const [userId, setClientId] = useState(null);
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const isClient = userProfile?.role?.name === 'Client';
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showOldPassword, setShowOldPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [url, setUrl] = useState('');
  const [permanentAddressLine1, setPermanentAddressLine1] = useState('');
  const [permanentAddressLine2, setPermanentAddressLine2] = useState('');
  const [permanentCity, setPermanentCity] = useState('');
  const [permanentState, setPermanentState] = useState('');
  const [permanentCountry, setPermanentCountry] = useState('');
  const [permanentZipCode, setPermanentZipCode] = useState('');
  const [addressLine1, setAddressLine1] = useState(userProfile.Address_line1 || '');
  const [addressLine2, setAddressLine2] = useState(userProfile.Address_line2 || '');
  const [city, setCity] = useState(userProfile.City || '');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [searchTermState, setSearchTermState] = useState('');
  const [filteredStates, setFilteredStates] = useState([]);
  const [filteredStatesPermanent, setFilteredStatesPermanent] = useState([]);
  const [dropdownOpenCity, setDropdownOpenCity] = useState(false);
  const [dropdownOpenState, setDropdownOpenState] = useState(false);
  const [state, setState] = useState(userProfile.State || '');
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredCities, setFilteredCities] = useState([]);
  const [zipCode, setZipCode] = useState(userProfile.Zip_code || '');
  const [Country, setCountry] = useState(userProfile.Country || '');
  const [dropdownOpenPermanentState, setDropdownOpenPermanentState] = useState(false);
  const [currentLoginTime, setCurrentLoginTime] = useState('');
  const [lastLoginTime, setLastLoginTime] = useState('');
  const [lastLogoutTime, setLastLogoutTime] = useState('');
  const [brokerLastLogin, setBrokerLastLogin] = useState('');
  const [brokerLastLogout, setBrokerLastLogout] = useState('');
  const [isTokenExpired, setIsTokenExpired] = useState(false);
  const toggleDropdown = () => setDropdownOpen(!dropdownOpen);
  const toggleDropdownState = () => setDropdownOpenState(!dropdownOpenState);
  const toggleDropdownCity = () => setDropdownOpenCity(!dropdownOpenCity);
  const toggleDropdownPermanentState = () => setDropdownOpenPermanentState(!dropdownOpenPermanentState);

  const handleChange = date => {
    setStartDate(date);
  };

  useEffect(() => {
    console.log("UseriiiiiiiiiiID:", userId);
    getUserProfile();
    getLastLogin();
    loadCityData();
    loadStateData();
    if (userId) {
      getClientLoginActivity();
      getBrokerLoginActivity();
    } else {
      console.log("User  ID is null, cannot fetch login activity.");
    }
  }, [userId]);

  const formatDateTime = (dateTime) => {
    if (!dateTime) return 'Not Logout';
    const date = new Date(dateTime);
    if (isNaN(date.getTime())) return 'Not Logout';
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${year}/${month}/${day}, ${hours}:${minutes}:${seconds}`;
  };

  const getClientLoginActivity = async () => {
    console.log("Fetching login activity for userId:", userId,);
    try {
      const loginActivityData = await fetchClientLoginActivity(userId);
      setCurrentLoginTime(formatDateTime(loginActivityData.current_login_time));
      setLastLoginTime(formatDateTime(loginActivityData.last_login_time));
      setLastLogoutTime(formatDateTime(loginActivityData.last_logout_time));
    } catch (error) {
      console.error("Error fetching client login activity:", error);
      setCurrentLoginTime('Not Found');
      setLastLoginTime('Not Found');
      setLastLogoutTime('Not Found');
    }
  };

  const getBrokerLoginActivity = async () => {
    console.log("Fetching broker login activity for userId:", userId);
    try {
      const loginActivityData = await getClientBrokerLoginActivity(userId);
      if (loginActivityData && loginActivityData.length > 0) {
        const activity = loginActivityData[0];
        setBrokerLastLogin(activity.last_login);
        setBrokerLastLogout(activity.logout_time ? activity.logout_time : 'N/A');
        setIsTokenExpired(activity.isTokenExpired);
      }
    } catch (error) {
      console.error("Error fetching broker login activity:", error);
      setBrokerLastLogin('Not Found');
      setBrokerLastLogout('Not Found');
      setIsTokenExpired(false);
    }
  };

  const loadCityData = async () => {
    try {
      const citiesData = await getCityData();
      if (Array.isArray(citiesData.data)) {
        setCities(citiesData.data);
        setFilteredCities(citiesData.data);
      } else {
        setCities([]);
        setFilteredCities([]);
      }
    } catch (error) {
      console.error("Error fetching city data:", error);
      setCities([]);
      setFilteredCities([]);
    }
  };

  const handleCitySearch = async (e) => {
    const searchValue = e.target.value;
    setSearchTerm(searchValue);

    if (searchValue) {
      try {
        const results = await searchCity(searchValue);
        console.log("sssssssssssssssssssssssss", results);

        setFilteredCities(results || []);
      } catch (error) {
        console.error("Error searching cities:", error);
        toast.error("Failed to search for cities.");
        setFilteredCities([]);
      }
    } else {
      setFilteredCities(cities);
    }
  };

  const handleCitySelect = async (selectedCity) => {
    setCity(selectedCity.name);
    setDropdownOpen(false);
    const filteredStates = states.filter(state => state.state_code === selectedCity.state_code);
    setFilteredStates(filteredStates)
    console.log("selectedCity", filteredStates);
    setState('');
  };

  const handleCitySelectPermanent = async (selectedCity) => {
    setUserProfile({ ...userProfile, permanentCity: selectedCity.name });
    setDropdownOpenCity(false);
    setPermanentCity(selectedCity.name);
    const filteredStates1 = states.filter(state => state.state_code === selectedCity.state_code);
    setFilteredStatesPermanent(filteredStates1)
    console.log("selectedCity", filteredStates1);

    setPermanentState('');

  };

  const loadStateData = async () => {
    try {
      const statesData = await getStateData();
      // Accessing the 'data' property
      if (Array.isArray(statesData.data)) {
        setStates(statesData.data);
        console.log('StatesData', statesData);
      } else {
        console.error('Expected states to be an array, but got:', statesData);
        setStates([]);
      }
    } catch (error) {
      console.error("Error fetching state data:", error);
    }
  };

  const handleStateSearch = async (e) => {
    const searchValue = e.target.value;
    setSearchTermState(searchValue);

    if (searchValue) {
      try {
        const results = await searchState(searchValue);
        setFilteredStates(results || []);
      } catch (error) {
        console.error("Error searching states:", error);
        setFilteredStates([]);
      }
    } else {
      setFilteredStates(states);
    }
  };

  const handleStateSelect = (selectedState) => {
    setState(selectedState);
    // setUserProfile({ ...userProfile, state: selectedState });
    setDropdownOpenState(false);
  };
  const handleStateSelectPermanentState = (selectedState) => {
    setDropdownOpenPermanentState(false)
    setPermanentState(selectedState);;
  };

  const getUserProfile = async () => {
    try {
      const data = await fetchUserProfile();
      console.log('FetchUserProfileData', data)
      setUserProfile({
        ...data,
        fullName: `${data.firstName} ${data.lastName}`,
      });

      setClientId(data.client);
      // Use correct fields for client start and end dates
      setStartDate(data.start_date_client ? new Date(data.start_date_client) : null);
      setEndDate(data.end_date_client ? new Date(data.end_date_client) : null);

      setUserProfileNew(data)

      setAddressLine1(data.current_add_line_1)
      setAddressLine2(data.current_add_line_2)
      setCountry(data.current_country)
      setZipCode(data.current_zip_code)
      setCity(data.current_city);
      // setUserProfile({ ...userProfile, city: data.current_city});
      setState(data.current_state);
      // setUserProfile({ ...userProfile, state: data.current_state});
      setPermanentAddressLine1(data.permanent_add_line_1)
      setPermanentAddressLine2(data.permanent_add_line_2)
      setPermanentCountry(data.permanent_country)
      setPermanentZipCode(data.permanent_zip_code)
      setPermanentCity(data.permanent_city);
      setPermanentState(data.permanent_state);

      setSameAddress(data.is_address_same);
      const profilePictureUrl = data.profilePicture
        ? `${baseUrl}${data.profilePicture}`
        : man;
      setUrl(profilePictureUrl);

    } catch (error) {
      console.error("Error fetching user profile:", error);
    }
  };

  const getLastLogin = async () => {
    try {
      const lastLoginData = await fetchLastLogin();
      console.log('Last login data:', lastLoginData);
      setLastLogin(lastLoginData.last_login_time);
      setLastIP(lastLoginData.last_ip);
    } catch (error) {
      console.error("Error fetching last login:", error);
    }
  };

  const formattedLastLogin = new Date(lastLogin).toLocaleString();

  const readUrl = (event) => {
    if (event.target.files.length === 0) return;
    const file = event.target.files[0];
    console.log("Selected file:", file);
    const mimeType = file.type;

    if (!mimeType.match(/image\/*/)) {
      return;
    }

    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = async () => {
      const imageUrl = reader.result;
      setUrl(imageUrl);
      try {
        await updateUserProfileImage(file); // Ensure this is the File object
        toast.success("Profile updated successfully!");
      } catch (error) {
        toast.error("Error updating profile: " + error.message);
      }
    };
  };

  const handleUserProfileUpdate = async (e) => {
    e.preventDefault();
    try {
      const updatedProfile = {
        fullName: userProfile.fullName,
        start_date_client: startDate?.toISOString().split('T')[0],
        end_date_client: endDate ? endDate.toISOString().split('T')[0] : null
      };
      await updateUserProfile(updatedProfile);
      toast.success("Profile updated successfully!");
    } catch (error) {
      toast.error("Error updating profile: " + error.message);
    }
  };

  const handleAddressUpdate = async (e) => {
    e.preventDefault();
    try {
      const updatedProfile = {
        current_add_line_1: addressLine1,
        current_add_line_2: addressLine2,
        current_city: city,
        current_state: state,
        current_country: Country,
        current_zip_code: zipCode,
        is_address_same: sameAddress,
        permanent_add_line_1: sameAddress ? addressLine1 : permanentAddressLine1,
        permanent_add_line_2: sameAddress ? addressLine2 : permanentAddressLine2,
        permanent_city: sameAddress ? city : permanentCity,
        permanent_state: sameAddress ? state : permanentState,
        permanent_country: sameAddress ? Country : permanentCountry,
        permanent_zip_code: sameAddress ? zipCode : permanentZipCode,
      };
      console.log('Payload for address update:', updatedProfile);

      const response = await updateAddress(updatedProfile);

      console.log('Response from updateUser Profile:', response);

      toast.success("Address updated successfully!");
      getUserProfile();
    } catch (error) {
      toast.error("Error updating address: " + error.message);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    const passwordRegex = /^(?=.*[A-Z])(?=.*[!@#$%^&*(),.?":{}|<>])(?=.*\d.*\d.*\d.*\d).{8,}$/;

    if (newPassword !== confirmPassword) {
      toast.error("New Password and Confirm Password do not match!");
      return;
    }

    if (!passwordRegex.test(newPassword)) {
      toast.error("Password must start with a first capital letter, contain a special character, 4 digits, with text.");
      return;
    }

    try {
      await changePassword(oldPassword, newPassword, confirmPassword);
      toast.success("Password changed successfully!");
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      toast.error(error.message);
    }
  };

  const handleSameAddressToggle = () => {
    setSameAddress(!sameAddress);
    if (!sameAddress) {
      // If the checkbox is checked, autofill the permanent address
      setPermanentAddressLine1(addressLine1);
      setPermanentAddressLine2(addressLine2);
      setPermanentCity(city);
      setPermanentState(state);
      setPermanentCountry(Country);
      setPermanentZipCode(zipCode);
    } else {
      setPermanentAddressLine1(userProfileNew.permanent_add_line_1)
      setPermanentAddressLine2(userProfileNew.permanent_add_line_2)
      setPermanentCountry(userProfileNew.permanent_country)
      setPermanentZipCode(userProfileNew.permanent_zip_code)
      setPermanentCity(userProfileNew.permanent_city);
      setPermanentState(userProfileNew.permanent_state);
    }
  };

  const togglePasswordVisibility = (passwordType) => {
    if (passwordType === 'old') {
      setShowOldPassword(!showOldPassword);
    } else if (passwordType === 'new') {
      setShowNewPassword(!showNewPassword);
    } else if (passwordType === 'confirm') {
      setShowConfirmPassword(!showConfirmPassword);
    }
  };

  return (
    <Container fluid>
      <ToastContainer />
      <Row className="justify-content-center">
        <Col md="10" style={{ width: '100%' }}>
          <Card>
            <CardBody>
              <Row style={{ minHeight: '400px' }}>
                {/* {/ Left Section: Profile Picture /} */}
                <Col md="4" className="border-right">
                  <div className="text-center">
                    <h5 className='userprofile-head'>User Profile</h5>
                    <div className='hovercard'>
                      <div className='user-image'>
                        <div className='avatar'>
                          <img src={url || man} className='step1 user-logo' alt='User Avatar' />
                        </div>
                        <div className='icon-wrapper step2' data-intro='Change Profile image here'>
                          <i className='icofont icofont-pencil-alt-5' >
                            <input className='upload' type='file' onChange={readUrl} />
                          </i>
                        </div>
                      </div>
                    </div>

                  </div>
                </Col>

                <Col md="8" className='content-col'>
                  <Nav tabs className="border-tab">
                    <NavItem>
                      <NavLink
                        className={activeTab === '1' ? 'active' : ''}
                        onClick={() => setActiveTab('1')}
                      >
                        <User style={{ marginBottom: '-6px' }} /> About Me
                      </NavLink>
                    </NavItem>

                    {isClient && (
                      <NavItem>
                        <NavLink
                          className={activeTab === '2' ? 'active' : ''}
                          onClick={() => setActiveTab('2')}
                        >
                          <Target style={{ marginBottom: '-6px' }} /> More Info.
                        </NavLink>
                      </NavItem>
                    )}

                    <NavItem>
                      <NavLink
                        className={activeTab === '3' ? 'active' : ''}
                        onClick={() => setActiveTab('3')}
                      >
                        <Info style={{ marginBottom: '-6px' }} /> Change Password
                      </NavLink>
                    </NavItem>

                    {isClient && (
                      <NavItem>
                        <NavLink
                          className={activeTab === '4' ? 'active' : ''}
                          onClick={() => setActiveTab('4')}
                        >
                          <Info style={{ marginBottom: '-6px' }} /> Login Activity
                        </NavLink>
                      </NavItem>
                    )}
                  </Nav>

                  <TabContent activeTab={activeTab}>
                    {/* Tab Content 1: About Me */}
                    <TabPane tabId="1">
                      <p style={{ fontSize: '18px', fontWeight: '500' }}>About Me</p>
                      <Form className="theme-form" onSubmit={handleUserProfileUpdate} encType="multipart/form-data">
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Full Name</Label>
                          <Col sm="8">
                            <Input
                              type="text"
                              value={userProfile.fullName}
                              onChange={(e) => setUserProfile({ ...userProfile, fullName: e.target.value })}
                              placeholder="Full Name"
                              readOnly={isClient}
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
                              readOnly={isClient}
                            />
                          </Col>
                        </FormGroup>

                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Last Login</Label>
                          <Col sm="8">
                            <Input type="text" value={formattedLastLogin} readOnly={isClient} />
                          </Col>
                        </FormGroup>

                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Last IP</Label>
                          <Col sm="8">
                            <Input type="text" value={lastIP} readOnly={isClient} />
                          </Col>
                        </FormGroup>

                        {isClient && (
                          <>
                            <FormGroup className="row">
                              <Label className="col-sm-4 col-form-label">Start Date</Label>
                              <Col sm="8">
                                <DatePicker
                                  className="form-control digits"
                                  selected={startDate}
                                  onChange={handleChange}
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
                          </>
                        )}
                      </Form>
                    </TabPane>

                    {/* Tab Content 2: Address */}
                    <TabPane tabId="2">
                      <p style={{ fontSize: '18px', fontWeight: '500' }}>Current Address</p>
                      <Form className="theme-form" onSubmit={handleAddressUpdate} encType="multipart/form-data">                        <FormGroup className="row">
                        <Label className="col-sm-4 col-form-label">Address 1</Label>
                        <Col sm="8">
                          <Input
                            type="text"
                            value={addressLine1}
                            onChange={(e) => setAddressLine1(e.target.value)}
                            placeholder="Address 1"

                          />
                        </Col>
                      </FormGroup>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Address 2</Label>
                          <Col sm="8">
                            <Input
                              type="text"
                              value={addressLine2}
                              onChange={(e) => setAddressLine2(e.target.value)}
                              placeholder="Address Line 2"
                            />
                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Country</Label>
                          <Col sm="8">
                            <Input
                              type="text"
                              value={Country}
                              onChange={(e) => setCountry(e.target.value)}
                              placeholder="Country"
                            />

                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">City</Label>
                          <Col sm="8">
                            <Dropdown isOpen={dropdownOpen} toggle={toggleDropdown}>
                              <DropdownToggle caret color="light" className="w-100">
                                {city || "Select City"}
                              </DropdownToggle>
                              <DropdownMenu className="w-100">
                                <Input
                                  type="text"
                                  value={searchTerm}
                                  onChange={handleCitySearch}
                                  placeholder="Search City"
                                  className="mx-2 my-2"
                                />
                                {Array.isArray(filteredCities) && filteredCities.length > 0 ? (
                                  filteredCities.map((city) => (
                                    <DropdownItem
                                      key={city.id}
                                      onClick={() => handleCitySelect(city)} // Pass the name or object as needed
                                    >
                                      {city.name}
                                    </DropdownItem>
                                  ))
                                ) : (
                                  <DropdownItem disabled>No cities found</DropdownItem>
                                )}
                              </DropdownMenu>
                            </Dropdown>
                          </Col>
                        </FormGroup>

                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">State</Label>
                          <Col sm="8">
                            <Dropdown isOpen={dropdownOpenState} toggle={toggleDropdownState}>
                              <DropdownToggle caret color="light" className="w-100">
                                {state || "Select State"}
                              </DropdownToggle>
                              <DropdownMenu className="w-100">
                                <Input
                                  type="text"
                                  value={searchTermState}
                                  onChange={handleStateSearch}
                                  placeholder="Search State"
                                  className="mx-2 my-2"
                                />
                                {/* Render state names instead of the entire object */}
                                {Array.isArray(filteredStates) && filteredStates.length > 0 ? (
                                  filteredStates.map((state) => (
                                    <DropdownItem
                                      key={state.id} // Use the unique id for the key
                                      onClick={() => handleStateSelect(state.name)} // Pass the name or object as needed
                                    >
                                      {state.name} {/* Access the name property */}
                                    </DropdownItem>
                                  ))
                                ) : (
                                  <DropdownItem disabled>No states found</DropdownItem>
                                )}
                              </DropdownMenu>
                            </Dropdown>
                          </Col>
                        </FormGroup>

                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Pincode</Label>
                          <Col sm="8">
                            <Input
                              type="text"
                              value={zipCode}
                              onChange={(e) => setZipCode(e.target.value)}
                              placeholder="Pincode"
                            />
                          </Col>
                        </FormGroup>

                        <FormGroup check className="row">
                          <Col sm="8" className="d-flex align-items-center">
                            <Input
                              type="checkbox"
                              checked={sameAddress}
                              onChange={(e) => handleSameAddressToggle()}
                              // onChange={handleSameAddressToggle}
                              style={{ marginRight: '8px', marginBottom: '6px', appearance: 'checkbox' }}
                            />
                            <p>Permanent Address Same as Current Address</p>
                          </Col>
                        </FormGroup>

                        {/* Permanent Address */}
                        {!sameAddress && (
                          <>
                            <p style={{ fontSize: '18px', fontWeight: '500' }}>Permanent Address</p>
                            <FormGroup className="row">
                              <Label className="col-sm-4 col-form-label">Permanent Address 1</Label>
                              <Col sm="8">
                                <Input
                                  type="text"
                                  value={permanentAddressLine1}
                                  onChange={(e) => setPermanentAddressLine1(e.target.value)}
                                  placeholder="Permanent Address 1"
                                />
                              </Col>
                            </FormGroup>
                            <FormGroup className="row">
                              <Label className="col-sm-4 col-form-label">Permanent Address 2</Label>
                              <Col sm="8">
                                <Input
                                  type="text"
                                  value={permanentAddressLine2}
                                  onChange={(e) => setPermanentAddressLine2(e.target.value)}
                                  placeholder="Permanent Address 2"
                                />
                              </Col>
                            </FormGroup>
                            <FormGroup className="row">
                              <Label className="col-sm-4 col-form-label">Permanent Country</Label>
                              <Col sm="8">
                                <Input
                                  type="text"
                                  value={permanentCountry}
                                  onChange={(e) => setPermanentCountry(e.target.value)}
                                  placeholder="Permanent Country"
                                />
                              </Col>
                            </FormGroup>
                            <FormGroup className="row">
                              <Label className="col-sm-4 col-form-label">Permanent City</Label>
                              <Col sm="8">
                                <Dropdown isOpen={dropdownOpenCity} toggle={toggleDropdownCity}>
                                  <DropdownToggle caret color="light" className="w-100">
                                    {permanentCity || "Select City"}
                                  </DropdownToggle>
                                  <DropdownMenu className="w-100">
                                    <Input
                                      type="text"
                                      value={searchTerm}
                                      onChange={handleCitySearch}
                                      placeholder="Search City"
                                      className="mx-2 my-2"
                                    />
                                    {Array.isArray(filteredCities) && filteredCities.length > 0 ? (
                                      filteredCities.map((city) => (
                                        <DropdownItem
                                          key={city.id}
                                          onClick={() => handleCitySelectPermanent(city)}
                                        >
                                          {city.name}
                                        </DropdownItem>
                                      ))
                                    ) : (
                                      <DropdownItem disabled>No cities found</DropdownItem>
                                    )}
                                  </DropdownMenu>
                                </Dropdown>
                              </Col>
                            </FormGroup>

                            <FormGroup className="row">
                              <Label className="col-sm-4 col-form-label">Permanent State</Label>
                              <Col sm="8">
                                <Dropdown isOpen={dropdownOpenPermanentState} toggle={toggleDropdownPermanentState}>
                                  <DropdownToggle caret color="light" className="w-100">
                                    {permanentState || "Select State"}
                                  </DropdownToggle>
                                  <DropdownMenu className="w-100">
                                    <Input
                                      type="text"
                                      value={searchTermState}
                                      onChange={handleStateSearch}
                                      placeholder="Search State"
                                      className="mx-2 my-2"
                                    />
                                    {Array.isArray(filteredStatesPermanent) && filteredStatesPermanent.length > 0 ? (
                                      filteredStatesPermanent.map((state) => (
                                        <DropdownItem
                                          key={state.id}
                                          onClick={() => handleStateSelectPermanentState(state.name)}
                                        >
                                          {state.name}
                                        </DropdownItem>
                                      ))
                                    ) : (
                                      <DropdownItem disabled>No states found</DropdownItem>
                                    )}
                                  </DropdownMenu>
                                </Dropdown>
                              </Col>
                            </FormGroup>

                            <FormGroup className="row">
                              <Label className="col-sm-4 col-form-label">Permanent Pincode</Label>
                              <Col sm="8">
                                <Input
                                  type="text"
                                  value={permanentZipCode}
                                  onChange={(e) => setPermanentZipCode(e.target.value)}
                                  placeholder="Permanent Pincode"
                                />
                              </Col>
                            </FormGroup>
                          </>
                        )}

                        <Button type="submit" className='search-btn-clr'>Update Address</Button>
                      </Form>
                    </TabPane>

                    {/* Tab Content 3: Change Password */}
                    <TabPane tabId="3">
                      <p style={{ fontSize: '18px', fontWeight: '500' }}>Change Password</p>
                      <Form className="theme-form" onSubmit={handlePasswordChange}>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Old Password</Label>
                          <Col sm="8" className="position-relative">
                            <Input
                              type={showOldPassword ? 'text' : 'password'}
                              placeholder="Enter Old Password"
                              value={oldPassword}
                              onChange={(e) => setOldPassword(e.target.value)}
                            // readOnly={isClient}
                            />
                            <div
                              className="position-absolute"
                              style={{ top: '28%', right: '22px', cursor: 'pointer' }}
                              onClick={() => togglePasswordVisibility('old')}
                            >
                              {showOldPassword ? <Eye /> : <EyeOff />}
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
                            // readOnly={isClient}
                            />
                            <div
                              className="position-absolute"
                              style={{ top: '28%', right: '22px', cursor: 'pointer' }}
                              onClick={() => togglePasswordVisibility('new')}
                            >
                              {showNewPassword ? <Eye /> : <EyeOff />}
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
                              onClick={() => togglePasswordVisibility('confirm')}
                            >
                              {showConfirmPassword ? <Eye /> : <EyeOff />}
                            </div>
                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Col sm="8" className="ml-auto">
                            <button type="submit" className="btn btn-primary search-btn-clr">Update Password</button>
                          </Col>
                        </FormGroup>
                      </Form>
                    </TabPane>

                    <TabPane tabId="4">
                      <p style={{ fontSize: '18px', fontWeight: '500' }}>Daily Login Activity</p>
                      <Form className="theme-form">
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Broker Login</Label>
                          <Col sm="8">
                            <Input type="text" value={brokerLastLogin || 'not found'} readOnly />
                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Broker Logout</Label>
                          <Col sm="8">
                            <Input type="text" value={brokerLastLogout || 'not found'} readOnly />
                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Token Expired</Label>
                          <Col sm="8">
                            <Input
                              type="text"
                              value={isTokenExpired ? "Token is expired" : "Token is not expired"}
                              readOnly
                              style={{ color: isTokenExpired ? 'red' : 'green' }}
                            />
                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Login</Label>
                          <Col sm="8">
                            <Input type="text" value={currentLoginTime || 'not found'} readOnly />
                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Last Login</Label>
                          <Col sm="8">
                            <Input type="text" value={lastLoginTime || 'not found'} readOnly />
                          </Col>
                        </FormGroup>
                        <FormGroup className="row">
                          <Label className="col-sm-4 col-form-label">Last Logout</Label>
                          <Col sm="8">
                            <Input type="text" value={lastLogoutTime || 'not found'} readOnly />
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
