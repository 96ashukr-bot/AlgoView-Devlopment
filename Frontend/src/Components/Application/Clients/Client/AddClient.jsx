import React, { useState, useEffect } from 'react';
import { Col, Card, CardHeader, CardBody, Form, Label, Row, Input, Button, Spinner, FormGroup } from 'reactstrap';
import { useNavigate } from 'react-router-dom';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { getSegmentsList, getSubSegment, getGroupServicesList, fetchSubAdminsList, addClient, getStrategies, getLicence } from '../../../../Services/Authentication';
import './Clients.css'

const LICENSE_NAMES = ['Demo', 'Live'];
const LICENSE_NAME_SET = new Set(LICENSE_NAMES.map((name) => name.toLowerCase()));
const DEMO_LICENSE_DAYS = 5;
const MONTH_OPTIONS = Array.from({ length: 12 }, (_, index) => index + 1);

const formatDateInput = (date) => date.toISOString().split('T')[0];

const getLicenseDates = (licenseName, monthsValue) => {
  if (!licenseName) {
    return { fromDate: '', toDate: '' };
  }

  const startDate = new Date();
  startDate.setHours(0, 0, 0, 0);
  const endDate = new Date(startDate);

  if (licenseName === 'Demo') {
    endDate.setDate(endDate.getDate() + DEMO_LICENSE_DAYS);
    return {
      fromDate: formatDateInput(startDate),
      toDate: formatDateInput(endDate),
    };
  }

  if (licenseName === 'Live') {
    const months = Number(monthsValue);
    if (!months) {
      return {
        fromDate: formatDateInput(startDate),
        toDate: '',
      };
    }
    endDate.setMonth(endDate.getMonth() + months);
    return {
      fromDate: formatDateInput(startDate),
      toDate: formatDateInput(endDate),
    };
  }

  return { fromDate: '', toDate: '' };
};

const AddClient = () => {
  const getStrategyModeState = (strategyIds = [], strategyList = []) => {
    const selected = strategyList.filter((strategy) => strategyIds.includes(strategy.id));
    return {
      indicator: selected.some((strategy) => strategy.execution_mode !== 'MULTI_LEG'),
      multiLeg: selected.some((strategy) => strategy.execution_mode === 'MULTI_LEG'),
    };
  };

  const [formData, setFormData] = useState({
    userName: '',
    fullName: '',
    email: '',
    phoneNumber: '',
    license: '',
    toDate: '',
    fromDate: '',
    // broker: '',
    segment: '',
    // subsegment: [],
    groupService: '',
    tomonth: '',
    // dematuserid: '',
    subadmin: '',
    switchOption: false,
    switchOptionSeg: false,
  });

  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const [segments, setSegments] = useState([]);
  const [subSegments, setSubSegments] = useState([]);
  const [licenses, setLicenses] = useState([]);
  const [groupServices, setGroupServices] = useState([]);
  const [subAdmins, setSubAdmins] = useState([]);
  const [strategies, setStrategies] = useState([]);
  const [subsegment, setSubSegment] = useState([]);
  const [selectedSubsegment, setSelectedSubsegment] = useState([]);
  const [selectedStrategies, setSelectedStrategies] = useState([]);
  const [selectedStrategyModes, setSelectedStrategyModes] = useState({ indicator: false, multiLeg: true });
  const [selectedGroupService, setSelectedGroupService] = useState(null);
  const availableLicenses = licenses.filter((license) => LICENSE_NAME_SET.has(String(license.name || '').trim().toLowerCase()));
  const isDemoLicense = formData.license === 'Demo';
  const isLiveLicense = formData.license === 'Live';
  const indicatorStrategies = strategies.filter((strategy) => strategy.execution_mode !== 'MULTI_LEG');
  const multiLegStrategies = strategies.filter((strategy) => strategy.execution_mode === 'MULTI_LEG');


  useEffect(() => {
    fetchSegments();
    // fetchSubSegments();
    festchLicenses();
    fetchGroupServices();
    fetchSubAdmins();
    fetchStrategies();
  }, []);

  useEffect(() => {
    if (formData.segment) {
      fetchSubSegments(); // Fetch subsegments whenever the selected segment changes
    }
  }, [formData.segment]);
  
  useEffect(() => {
    setSelectedStrategyModes(getStrategyModeState(selectedStrategies, strategies));
  }, [selectedStrategies, strategies]);

  useEffect(() => {
    if (!formData.license) {
      return;
    }

    const { fromDate, toDate } = getLicenseDates(formData.license, formData.tomonth);
    setFormData((prevData) => {
      if (prevData.fromDate === fromDate && prevData.toDate === toDate) {
        return prevData;
      }
      return {
        ...prevData,
        fromDate,
        toDate,
      };
    });
  }, [formData.license, formData.tomonth]);
  
  // When License is Selected
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;

    if (type === 'checkbox') {
      setFormData(prevData => ({
        ...prevData,
        [name]: checked,
      }));
    } else {
      let newValue = value;

      // Convert segment to integer
      if (name === 'segment') {
        newValue = parseInt(value);
      } else if (name === 'groupService') {
        newValue = parseInt(value);
      }

      if (name === 'license') {
        const licenseDates = getLicenseDates(newValue, '');
        setFormData(prevData => ({
          ...prevData,
          license: newValue,
          tomonth: '',
          fromDate: licenseDates.fromDate,
          toDate: licenseDates.toDate,
        }));
      } else if (name === 'tomonth') {
        const licenseDates = getLicenseDates(formData.license, newValue);
        setFormData(prevData => ({
          ...prevData,
          tomonth: newValue,
          fromDate: licenseDates.fromDate,
          toDate: licenseDates.toDate,
        }));
      } else if (name === 'subsegment') {
        const selectedValues = Array.from(e.target.selectedOptions, option => parseInt(option.value));
        setFormData(prevData => ({
          ...prevData,
          [name]: selectedValues,
        }));
      } else {
        setFormData(prevData => ({
          ...prevData,
          [name]: newValue,
        }));
      }

      if (name === 'groupService') {
        const selectedService = groupServices.find(service => service.id === parseInt(value));
        setSelectedGroupService(selectedService ? selectedService : null);
        applyGroupServiceStrategies(selectedService);

        const test = [];
        if (selectedService && selectedService.json_data) { // Check if selectedService and json_data exist
          Object.entries(subSegments).forEach(([key, value]) => {
            Object.entries(selectedService.json_data).forEach(([key1, value1]) => {
              if (value.name === (value1.ScriptName || value1.ServiceName)) {
                test.push(value.id);
              }
            });
          });
        }
        setSelectedSubsegment(test);
      }
    }

    setErrors(prevErrors => ({ ...prevErrors, [name]: '' }));
  };

  const fetchSegments = async () => {
    try {
      const response = await getSegmentsList();
      console.log('Segments API Response:', response);

      // Check if the response itself is an array
      if (response && Array.isArray(response)) {
        setSegments(response);

        if (response.length > 0) {
          // Define the desired segment name
          const desiredSegmentName = 'Option';

          // Find the segment by name using `.find`
          const foundSegment = response.find(
            segment => segment.name.toLowerCase() === desiredSegmentName.toLowerCase()
          );

          // If the segment is found, update the formData
          if (foundSegment) {
            setFormData(prevData => ({
              ...prevData,
              segment: foundSegment.id,
            }));
            console.log(`Segment ID for ${desiredSegmentName}:`, foundSegment.id);
          } else {
            console.error(`Segment with name "${desiredSegmentName}" not found.`);
          }
        }
      } else {
        console.error('Unexpected API response structure. Expected an array:', response);
        setSegments([]);
      }
    } catch (error) {
      console.error('Error fetching Segments:', error);
      toast.error('Failed to load Segments.');
      setSegments([]);
    }
  };

  const fetchSubSegments = async () => {
    try {
      const response = await getSubSegment(formData.segment);
      console.log('SubSegments API Response:', response);

      // Access the client_segment_list from the response
      if (response && Array.isArray(response.client_segment_list)) {
        setSubSegments(response.client_segment_list);
        console.log('Subsegments set:', response.client_segment_list);
      } else {
        console.error('Fetched SubSegments are not an array:', response);
        setSubSegments([]);
      }
    } catch (error) {
      console.error('Error fetching SubSegments:', error);
      toast.error('Failed to load SubSegments.');
      setSubSegments([]);
    }
  };

  const fetchGroupServices = async () => {
    try {
      const response = await getGroupServicesList();
      if (response && Array.isArray(response)) {
        setGroupServices(response);
      } else {
        console.error("Fetched group services are not an array:", response);
        setGroupServices([]);
      }
    } catch (error) {
      console.error("Error fetching group services:", error);
      setGroupServices([]);
    }
  };


  const festchLicenses = async () => {
    try {
      const response = await getLicence();
      console.log('License Response:', response);
      const licenseRows = Array.isArray(response?.results) ? response.results : Array.isArray(response) ? response : [];
      if (licenseRows.length) {
        setLicenses(licenseRows.filter((license) => LICENSE_NAME_SET.has(String(license.name || '').trim().toLowerCase())));
      } else {
        console.error('Fetched licenses are not an array:', response);
        setLicenses([]);
      }
    }
    catch (error) {
      console.error('Error fetching licenses:', error);
      setLicenses([]);
    }
  };


  const fetchSubAdmins = async () => {
    try {
      const response = await fetchSubAdminsList();
      console.log('Fetched Sub Admins:', response);
      if (response && Array.isArray(response)) {
        setSubAdmins(response);
      } else {
        console.error('Fetched sub admins are not an array:', response);
        setSubAdmins([]);
      }
    } catch (error) {
      console.error('Error fetching sub admins:', error);
      toast.error('Failed to load sub admins.');
      setSubAdmins([]);
    }
  };

  const fetchStrategies = async () => {
    try {
      const response = await getStrategies(1, 500);
      console.log('Response:', response);

      const strategies = response?.results;

      if (Array.isArray(strategies)) {
        console.log('Fetched strategies:', strategies);
        setStrategies(strategies);
      } else {
        console.error('Fetched strategies are not an array:', strategies);
        toast.error('Invalid strategies data.');
        setStrategies([]);
      }
    } catch (error) {
      console.error('Error fetching strategies:', error);
      toast.error('Failed to load strategies.');
      setStrategies([]);
    }
  };

  const applyGroupServiceStrategies = (groupService) => {
    if (!groupService || !Array.isArray(groupService.Strategy)) {
      return;
    }

    const groupStrategyIds = groupService.Strategy.map((strategy) => strategy.id);
    if (!groupStrategyIds.length) {
      return;
    }

    setSelectedStrategies((prev) => {
      const nonIndicatorStrategies = prev.filter((strategyId) => {
        const matchingStrategy = strategies.find((strategy) => strategy.id === strategyId);
        return matchingStrategy?.execution_mode === 'MULTI_LEG';
      });
      return Array.from(new Set([...nonIndicatorStrategies, ...groupStrategyIds]));
    });
    setSelectedStrategyModes((prev) => ({
      ...prev,
      indicator: true,
    }));
  };

  const handleStrategyModeToggle = (modeKey) => {
    const nextEnabled = !selectedStrategyModes[modeKey];
    setSelectedStrategyModes((prev) => ({
      ...prev,
      [modeKey]: nextEnabled,
    }));

    if (!nextEnabled) {
      setSelectedStrategies((prev) => prev.filter((strategyId) => {
        const matchingStrategy = strategies.find((strategy) => strategy.id === strategyId);
        if (!matchingStrategy) {
          return false;
        }
        if (modeKey === 'indicator') {
          return matchingStrategy.execution_mode === 'MULTI_LEG';
        }
        return matchingStrategy.execution_mode !== 'MULTI_LEG';
      }));
    }
  };

  const handleCheckboxChange = (strategy) => {
    if (!strategy) return;

    if (selectedStrategies.includes(strategy.id)) {
      setSelectedStrategies(selectedStrategies.filter((id) => id !== strategy.id));
    } else {
      setSelectedStrategies([...selectedStrategies, strategy.id]);
    }
  };

  const handleCheckboxChangesegment = (subsegment) => {
    if (!subsegment) {
      console.error('subsegment is undefined');
      return;
    }

    console.log("vvvvvvvvvvvvvvvvvvvvvv", selectedSubsegment)


    // Check if the subsegment is already selected
    if (selectedSubsegment.includes(subsegment.id)) {
      // Remove it if already selected
      setSelectedSubsegment(selectedSubsegment.filter(id => id !== subsegment.id));
    } else {
      // Add it to the selected strategies
      setSelectedSubsegment([...selectedSubsegment, subsegment.id]);
    }
  };

  const validateForm = () => {
    const errors = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const mobileRegex = /^[0-9]{10}$/;

    if (!formData.userName?.trim()) {
      errors.userName = 'User Name is required';
    }

    if (formData.email && !emailRegex.test(formData.email)) {
      errors.email = 'Format of email is incorrect';
    }

    if (formData.phoneNumber && !mobileRegex.test(formData.phoneNumber)) {
      errors.phoneNumber = 'Number must be 10 digits only';
    }

    if (!formData.license) {
      errors.license = 'License is required';
    }

    if (isLiveLicense) {
      if (!formData.tomonth) errors.tomonth = 'This field is required';
    }

    console.log("Form validation errors: ", errors);
    return errors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validateForm();
    if (Object.keys(validationErrors).length) {
      setErrors(validationErrors);
      // toast.error('Please fill out all required fields.');
      return;
    }
    // console.log('Broker before submission:', formData.broker);
    setLoading(true);

    const selectedLicense = availableLicenses.find(license => license.name.toLowerCase() === formData.license.toLowerCase());
    const licenseId = selectedLicense ? selectedLicense.id : null;

    let payload = {
      userName: formData.userName,
      client_status: true,
    };

    if (formData.email) payload.email = formData.email;
    if (formData.fullName) payload.fullName = formData.fullName;
    if (formData.phoneNumber) payload.phoneNumber = formData.phoneNumber;
    if (formData.groupService) payload.Group_service = formData.groupService;
    if (formData.subadmin) payload.assigned_client = formData.subadmin;
    if (licenseId) payload.license = licenseId;
    if (formData.segment) payload.segment = formData.segment;
    if (selectedSubsegment.length) payload.subsegment = selectedSubsegment;
    if (selectedStrategies.length) payload.Strategy = selectedStrategies;

    console.log('Payload before sending to API:', payload);

    if (licenseId) {
      const licenseName = selectedLicense.name.toLowerCase();
      if (licenseName === 'live') {
        payload = {
          ...payload,
          to_month: formData.tomonth,
        };
      }
    }

    try {
      await addClient(payload);
      toast.success('Client added successfully!');
      setFormData({
        userName: '',
        fullName: '',
        email: '',
        phoneNumber: '',
        license: '',
        toDate: '',
        fromDate: '',
        // broker: '',
        segment: '',
        subsegment: '',
        groupService: '',
        tomonth: '',
        // dematuserid: '',
        subadmin: '',
        switchOption: false,
        switchOptionSeg: false,
      });
      setErrors({});
      setTimeout(() => {
        setLoading(false);
        navigate('/client/all-clients-list');
      }, 1500);
    } catch (error) {
      console.error('Error:', error.message);

      if (error.message === "user with this email already exists.") {
        setErrors((prevErrors) => ({
          ...prevErrors,
          email: error.message, // Update email-specific error
        }));
      } else if (error.message === "A user with this phone number already exists.") {
        setErrors((prevErrors) => ({
          ...prevErrors,
          phoneNumber: error.message, // Update phone number-specific error
        }));
      } else {
        toast.error(error.message);
      }
      setLoading(false);
    }
  };

  const handleCancel = () => {
    navigate('/client/all-clients-list');
  };

  return (
    <>
      <ToastContainer />
      <Col sm="12">
        <Card className="mt-5">
          <CardHeader>
            <h5>Add Client</h5>
          </CardHeader>
          <CardBody>
            <Form className="needs-validation" noValidate onSubmit={handleSubmit}>
              <Row>
                <Col md="4 mb-3">
                  <Label htmlFor="userName">User Name
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="text"
                    className={`form-control ${errors.userName ? 'is-invalid' : ''} custom-input-style`}
                    name="userName"
                    id="userName"
                    placeholder="Enter User Name"
                    value={formData.userName}
                    onChange={handleChange}
                  />
                  {errors.userName && <div className="invalid-feedback text-danger">{errors.userName}</div>}
                </Col>

                <Col md="4 mb-3">
                  <Label htmlFor="fullName">Full Name</Label>
                  <Input
                    type="text"
                    className={`form-control ${errors.fullName ? 'is-invalid' : ''} custom-input-style`}
                    name="fullName"
                    id="fullName"
                    placeholder="Enter Full Name"
                    value={formData.fullName}
                    onChange={handleChange}
                  />
                  {errors.fullName && <div className="invalid-feedback text-danger">{errors.fullName}</div>}
                </Col>

                <Col md="4" className="mb-3">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    type="email"
                    className={`form-control ${errors.email ? 'is-invalid' : ''} custom-input-style`}
                    name="email"
                    id="email"
                    placeholder="Enter Email"
                    value={formData.email}
                    onChange={handleChange}
                  />
                  {errors.email && <div className="invalid-feedback text-danger">{errors.email}</div>}
                </Col>

                <Col md="4" className="mb-3">
                  <Label htmlFor="phoneNumber">Mobile</Label>
                  <Input
                    type="text"
                    className={`form-control ${errors.phoneNumber ? 'is-invalid' : ''} custom-input-style`}
                    name="phoneNumber"
                    id="phoneNumber"
                    placeholder="Enter Mobile No."
                    value={formData.phoneNumber}
                    onChange={handleChange}
                  />
                  {errors.phoneNumber && <div className="invalid-feedback text-danger">{errors.phoneNumber}</div>}
                </Col>


                {/* License Field */}
                <Col md="4 mb-3">
                  <Label htmlFor="license">License</Label>
                  <Input
                    type="select"
                    className={`form-control ${errors.license ? 'is-invalid' : ''} custom-input-style`}
                    name="license"
                    id="license"
                    value={formData.license}
                    onChange={handleChange}
                  >

                    {/* Handle License Based on Selected Option */}
                    <option value="">Select License</option>
                    {availableLicenses.map((license) => {
                      const normalizedName = LICENSE_NAMES.find((name) => name.toLowerCase() === String(license.name || '').trim().toLowerCase());
                      return (
                      <option key={license.id || normalizedName} value={normalizedName}>
                        {normalizedName}
                      </option>
                    )})}
                  </Input>
                  {errors.license && <div className="invalid-feedback text-danger">{errors.license}</div>}
                </Col>

                <Col md="4 mb-3">
                  <Label htmlFor="groupService">Group Service</Label>
                  <Input
                    type="select"
                    name="groupService"
                    id="groupService"
                    className='custom-input-style'
                    value={formData.groupService}
                    onChange={handleChange}
                  >
                    <option value="">Select Group Service</option>
                    {groupServices.map((service, index) => (
                      <option key={index} value={service.id}>
                        {service.group_name}
                      </option>
                    ))}
                  </Input>
                  {errors.groupService && <div className="invalid-feedback text-danger">{errors.groupService}</div>}
                </Col>

                <Col md="4 mb-3">
                  <Label htmlFor="subadmin">Sub Admin</Label>
                  <Input
                    type="select"
                    className={`form-control ${errors.subadmin ? 'is-invalid' : ''} custom-input-style`}
                    name="subadmin"
                    id="subadmin"
                    value={formData.subadmin}
                    onChange={handleChange}
                  >
                    <option value="">Select Sub-Admin</option>
                    {subAdmins.map((user, index) => (
                      <option key={index} value={user.id}>
                        {user.firstName} {user.lastName}
                      </option>
                    ))}
                  </Input>
                  {errors.subadmin && <div className="invalid-feedback text-danger">{errors.subadmin}</div>}
                </Col>

                {/* Conditional fields for Live license */}
                {formData.license === 'Live' && (
                  <>
                    <Col md="4 mb-3">
                      <Label htmlFor="tomonth">To Month
                        <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                      </Label>
                      <Input
                        type="select"
                        className={`form-control ${errors.tomonth ? 'is-invalid' : ''} custom-input-style`}
                        name="tomonth"
                        id="tomonth"
                        value={formData.tomonth}
                        onChange={handleChange}
                        required
                      >
                        <option value="">Select Month</option>
                        {MONTH_OPTIONS.map((month) => (
                          <option key={month} value={month}>
                            {month}
                          </option>
                        ))}
                      </Input>
                      {errors.tomonth && <div className="invalid-feedback text-danger">{errors.tomonth}</div>}
                    </Col>

                    <Col md="4 mb-3">
                      <Label htmlFor="fromDate">Service Start Date</Label>
                      <Input
                        type="date"
                        className="form-control custom-input-style"
                        name="fromDate"
                        id="fromDate"
                        value={formData.fromDate}
                        readOnly
                      />
                    </Col>

                    <Col md="4 mb-3">
                      <Label htmlFor="toDate">Service End Date</Label>
                      <Input
                        type="date"
                        className="form-control custom-input-style"
                        name="toDate"
                        id="toDate"
                        value={formData.toDate}
                        readOnly
                      />
                    </Col>
                  </>
                )}

                {/* Conditional fields for Demo license */}
                {formData.license === 'Demo' && (
                  <>
                    <Col md="4 mb-3">
                      <Label htmlFor="fromDate">Service Start Date</Label>
                      <Input
                        type="date"
                        className="form-control custom-input-style"
                        name="fromDate"
                        id="fromDate"
                        value={formData.fromDate}
                        readOnly
                      />
                    </Col>

                    <Col md="4 mb-3">
                      <Label htmlFor="toDate">Service End Date</Label>
                      <Input
                        type="date"
                        className="form-control custom-input-style"
                        name="toDate"
                        id="toDate"
                        value={formData.toDate}
                        readOnly
                      />
                    </Col>
                  </>
                )}

                <Col md="12" className="mt-4">
                  <h5>Segments</h5>
                </Col>

                <Col md="12" className="mt-4">
                  {subSegments.map((subsegment) => (
                    <label key={subsegment.id} style={{ width: '30%', paddingBottom: '20px', display: 'inline-flex' }}>
                      <input
                        type="checkbox"
                        style={{
                          marginLeft: '20px',
                          transform: 'scale(1.3)',
                          transformOrigin: 'center',
                        }}
                        disabled
                        checked={selectedSubsegment.includes(subsegment.id)}
                        onChange={() => handleCheckboxChangesegment(subsegment)}
                      />
                      <span style={{ marginLeft: '5px' }}>{subsegment.name}</span>
                    </label>
                  ))}
                </Col>
                {/* )} */}

                <Col md="12" className="mt-4">
                  {selectedGroupService && (
                    <Row>
                      {console.log("Selected Group Service JSON Data:", selectedGroupService.json_data)}
                      {selectedGroupService.json_data.map((service, index) => (
                        <Col md="auto" className="mt-3" key={index}>
                          <div
                            style={{
                              backgroundColor: "#283F7B",
                              border: '##283F7B',
                              color: "white",
                              borderRadius: '0px',
                              padding: '10px 12px',
                              cursor: 'default',
                              userSelect: 'none'
                            }}
                          >
                            {(service.ScriptName || service.ServiceName)}[O]
                          </div>
                        </Col>
                      ))}
                    </Row>
                  )}
                </Col>

                <Col md="12" className="mt-2 pb-2 pt-1">
                  <h6>All Group Services</h6>
                </Col>

                <Col md="12" className="mt-4 p-2">
                  <h5>Strategies</h5>
                </Col>

                <Col md="12" className="mt-4">
                  <div className="d-flex flex-wrap gap-4 mb-3">
                    <label style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                      <input
                        type="checkbox"
                        checked={selectedStrategyModes.indicator}
                        onChange={() => handleStrategyModeToggle('indicator')}
                      />
                      <span>Indicator Based Strategies</span>
                    </label>
                    <label style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                      <input
                        type="checkbox"
                        checked={selectedStrategyModes.multiLeg}
                        onChange={() => handleStrategyModeToggle('multiLeg')}
                      />
                      <span>Multi Leg Option Strategies</span>
                    </label>
                  </div>
                </Col>

                {selectedStrategyModes.indicator && (
                <Col md="12" className="mt-1">
                  <h6 className="mb-3">Indicator Based Strategies</h6>
                  {indicatorStrategies.map((strategy) => (
                    <label key={strategy.id} style={{ width: '30%', paddingBottom: '20px', display: 'inline-flex' }}>
                      <input
                        type="checkbox"
                        style={{
                          marginLeft: '20px',
                          transform: 'scale(1.3)',
                          transformOrigin: 'center',
                        }}
                        checked={selectedStrategies.includes(strategy.id)}
                        onChange={() => handleCheckboxChange(strategy)}
                      />
                      <span style={{ marginLeft: '5px' }}>{strategy.name}</span>
                    </label>
                  ))}
                </Col>
                )}

                <Col md="12" className="mt-2">
                  <h6 className="mb-3">Multi Leg Option Strategies</h6>
                  {multiLegStrategies.length > 0 ? multiLegStrategies.map((strategy) => (
                    <label key={strategy.id} style={{ width: '30%', paddingBottom: '20px', display: 'inline-flex' }}>
                      <input
                        type="checkbox"
                        style={{
                          marginLeft: '20px',
                          transform: 'scale(1.3)',
                          transformOrigin: 'center',
                        }}
                        checked={selectedStrategies.includes(strategy.id)}
                        onChange={() => handleCheckboxChange(strategy)}
                      />
                      <span style={{ marginLeft: '5px' }}>
                        {strategy.name}
                        {strategy.multi_leg_template_label ? ` (${strategy.multi_leg_template_label})` : ''}
                      </span>
                    </label>
                  )) : (
                    <p className="text-muted">No multi leg strategies available.</p>
                  )}
                </Col>

                <Col md="12 mb-3">
                  <Button type="submit" color="primary" className="search-btn-clr mt-3" disabled={loading}>
                    {loading ? <Spinner size="sm" /> : 'Add'}
                  </Button>
                  <Button
                    type="button"
                    color="danger"
                    className="mt-3 ms-2"
                    onClick={handleCancel}
                  >
                    Cancel
                  </Button>
                </Col>
              </Row>
            </Form>
          </CardBody>
        </Card>
      </Col>
    </>
  );
};

export default AddClient;
