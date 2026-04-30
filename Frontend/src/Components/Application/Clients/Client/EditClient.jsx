import React, { useState, useEffect } from 'react';
import { Col, Card, CardHeader, CardBody, Form, Label, Row, Input, Button, Spinner, FormGroup } from 'reactstrap';
import { useNavigate, useParams } from 'react-router-dom';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './Clients.css'
import { getSegmentsList, getSubSegment, getBroker, getGroupServicesList, fetchSubAdminsList, getClientById, updateClient, getStrategies, getLicence } from '../../../../Services/Authentication';

const LICENSE_NAMES = ['Demo', 'Live'];
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
    endDate.setDate(endDate.getDate() + 3);
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

const EditClient = () => {
  const getStrategyModeState = (strategyIds = [], strategyList = []) => {
    const selected = strategyList.filter((strategy) => strategyIds.includes(strategy.id));
    return {
      indicator: selected.some((strategy) => strategy.execution_mode !== 'MULTI_LEG'),
      multiLeg: selected.some((strategy) => strategy.execution_mode === 'MULTI_LEG'),
    };
  };

  const { id } = useParams();
  const [formData, setFormData] = useState({
    userName: '',
    fullName: '',
    email: '',
    mobile: '',
    license: '',
    toDate: '',
    fromDate: '',
    segment: '',
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
  // const [segmentID, setSegmentID] = useState('');
  const [subSegments, setSubSegments] = useState([]);
  const [brokers, setBrokers] = useState([]);
  const [licenses, setLicenses] = useState([]);
  const [groupServices, setGroupServices] = useState([]);
  const [subAdmins, setSubAdmins] = useState([]);
  const [strategies, setStrategies] = useState([]);
  const [selectedSubsegment, setSelectedSubsegment] = useState([]);
  const [selectedStrategies, setSelectedStrategies] = useState([]);
  const [selectedStrategyModes, setSelectedStrategyModes] = useState({ indicator: false, multiLeg: true });
  const [licensecond, setLicensesCond] = useState('');
  const [selectedGroupService, setSelectedGroupService] = useState(null);
  const availableLicenses = licenses.filter((license) => LICENSE_NAMES.includes(license.name));
  const indicatorStrategies = strategies.filter((strategy) => strategy.execution_mode !== 'MULTI_LEG');
  const multiLegStrategies = strategies.filter((strategy) => strategy.execution_mode === 'MULTI_LEG');

  useEffect(() => {
    fetchSegments();
    fetchBrokers();
    fetchGroupServices();
    fetchLicenses()
    fetchSubAdmins();
  }, []);
  useEffect(() => {
    if (id) {
      fetchClientData(id);
    }
    fetchStrategies();
  }, [id]);

  useEffect(() => {
    setSelectedStrategyModes(getStrategyModeState(selectedStrategies, strategies));
  }, [selectedStrategies, strategies]);

  const fetchClientData = async (clientId) => {
    try {
      const response = await getClientById(clientId);
      console.log('client data responseeeeee', response);

      if (response) {
        const primaryTradeSetting = response.client_trade_settings?.[0] || null;
        const resolvedSegmentId =
          primaryTradeSetting?.sub_segment?.segment ||
          response.Group_service?.segment?.id ||
          '';

        console.log('response.client_trade_settings', response.client_trade_settings);
        console.log('resolvedSegmentId', resolvedSegmentId);


        setFormData({
          userName: response.userName || '',
          fullName: response.fullName || '',
          email: response.email || 'switchOptionSeg',
          mobile: response.phoneNumber || '',
          license: response.license ? response.license.id : '',
          groupService: response.Group_service ? response.Group_service.id : '',
          tomonth: response.to_month || '',
          // dematuserid: response.demate_acc_uid || '',
          subadmin: response.assigned_client ? response.assigned_client.id : '',
          fromDate: response.start_date_client || '',
          toDate: response.end_date_client || '',
          segment: resolvedSegmentId,
          subsegment: primaryTradeSetting?.sub_segment?.id ? [primaryTradeSetting.sub_segment.id] : [],
          switchOption: true,
          switchOptionSeg: true,
          // segment: '',
        });
        setLicensesCond(response.license?.name || '');


        setSelectedGroupService(response.Group_service || null);

        // Fetch subsegments based on the selected segment
        if (response.client_trade_settings.length > 0) {
          // setFormData(prevData => ({
          //   ...prevData,
          //   switchOptionSeg: true
          // }));
          console.log("Subsegment Reponse for if **********************");
          if (response.client_trade_settings && Array.isArray(response.client_trade_settings)) {
            const selectedSubsegment = response.client_trade_settings.map(setting => setting.sub_segment.id);
            console.log('hhhhhhhhhhhhhhhh', selectedSubsegment)
            setSelectedSubsegment(selectedSubsegment);
          }

          if (resolvedSegmentId) {
            fetchSubSegments(resolvedSegmentId);
          }
        } else {
          console.log("Subsegment Reponse ###################");

          if (response.client_trade_settings && Array.isArray(response.client_trade_settings)) {
            const selectedSubsegment = response.client_trade_settings.map(setting => setting.sub_segment.id);
            console.log('hhhhhhhhhhhhhhhh', selectedSubsegment);
            if (resolvedSegmentId) {
              fetchSubSegments(resolvedSegmentId);
            }
          }
        }

        if (response.Strategy && Array.isArray(response.Strategy)) {
          const selectedStrategyIds = response.Strategy.map(strategy => strategy.id);
          setSelectedStrategies(selectedStrategyIds);
        }

        fetchStrategies();

        console.log('Updated formData:', formData);
      } else {
        toast.error('Failed to load client data.');
      }
    } catch (error) {
      console.error('Error fetching client data:', error.message);
      toast.error(error.message || 'Failed to load client data.');
    }
  };

  const licenceName = (licenseId) => {
    const licensecondition = licenses.find((licenseKey) => licenseKey.id === Number(licenseId));
    setLicensesCond(licensecondition?.name || '');
  };

  useEffect(() => {
    if (!licensecond) {
      return;
    }

    const { fromDate, toDate } = getLicenseDates(licensecond, formData.tomonth);
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
  }, [licensecond, formData.tomonth]);

  const fetchSegments = async () => {
    try {
      const response = await getSegmentsList();
      console.log('Segments API Response:', response);

      // Check if response is an array
      if (response && Array.isArray(response)) {
        setSegments(response);
      } else {
        console.error('Fetched Segments are not an array or invalid:', response);
        setSegments([]);
      }
    } catch (error) {
      console.error('Error fetching Segments:', error);
      toast.error('Failed to load Segments.');
      setSegments([]);
    }
  };

  const fetchSubSegments = async (segmentId = formData.segment) => {
    try {
      if (!segmentId) {
        setSubSegments([]);
        return;
      }

      const response = await getSubSegment(segmentId);
      console.log('SubSegments API Response:', response);

      // Validate and set the sub-segments
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


  const fetchBrokers = async () => {
    try {
      const response = await getBroker();
      setBrokers(response && Array.isArray(response) ? response : []);
    } catch (error) {
      toast.error('Failed to load brokers.');
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

  const fetchLicenses = async () => {
    try {
      const response = await getLicence();
      const fetchedLicenses = response && Array.isArray(response.results)
        ? response.results.filter((license) => LICENSE_NAMES.includes(license.name))
        : [];
      // Set licenses in state
      setLicenses(fetchedLicenses);
    } catch (error) {
      toast.error('Failed to load licenses.');
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
        fetchSubSegments(newValue);
      } else if (name === 'groupService') {
        newValue = parseInt(value);
      }

      if (name === 'subSegment') {
        const selectedValues = Array.from(e.target.selectedOptions, option => parseInt(option.value));
        setFormData(prevData => ({
          ...prevData,
          [name]: selectedValues,
        }));
        fetchSubSegments();
      } else {
        if (name === 'license') {
          const nextLicense = licenses.find((license) => license.id === Number(value));
          const nextLicenseName = nextLicense?.name || '';
          const licenseDates = getLicenseDates(nextLicenseName, '');
          setLicensesCond(nextLicenseName);
          setFormData((prevData) => ({
            ...prevData,
            license: value,
            tomonth: '',
            fromDate: licenseDates.fromDate,
            toDate: licenseDates.toDate,
          }));
          setErrors((prevErrors) => ({ ...prevErrors, [name]: '' }));
          return;
        }

        if (name === 'tomonth') {
          const licenseDates = getLicenseDates(licensecond, value);
          setFormData((prevData) => ({
            ...prevData,
            tomonth: value,
            fromDate: licenseDates.fromDate,
            toDate: licenseDates.toDate,
          }));
          setErrors((prevErrors) => ({ ...prevErrors, [name]: '' }));
          return;
        }

        setFormData(prevData => ({
          ...prevData,
          [name]: newValue,
        }));
      }

      // Check if the field changed is groupService
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

    console.log('Updated Form Data:', { ...formData, [name]: value });
    setErrors((prevErrors) => ({ ...prevErrors, [name]: '' }));
  };

  const validateForm = () => {
    const newErrors = {};
    ['userName', 'fullName', 'email', 'mobile', 'license', 'groupService', 'subadmin'].forEach((field) => {
      if (!formData[field]) {
        newErrors[field] = 'This field is required';
      }
    });

    if (licensecond === 'Live' && !formData.tomonth) {
      newErrors.tomonth = 'This field is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    console.log('Form Data Before Validation:', formData);
    console.log('Selected Strategies:', selectedStrategies);
    console.log('Selected SubSegment:', selectedSubsegment);


    if (!validateForm()) {
      toast.error('Please fill out all required fields.');
      return;
    }

    setLoading(true);
    // Prepare the payload
    const payload = {
      email: formData.email,
      userName: formData.userName,
      fullName: formData.fullName,
      phoneNumber: formData.mobile,
      license: formData.license,
      start_date_client: formData.fromDate,
      end_date_client: formData.toDate,
      // Broker: formData.broker,
      Group_service: formData.groupService,
      to_month: formData.tomonth,
      // givenservices_to_month: formData.serviceGivenToMonth,
      Strategy: selectedStrategies,
      segment: formData.segment,
      // subsegment: formData.subsegment,
      subsegment: selectedSubsegment,
      // demate_acc_uid: formData.dematuserid,
      assigned_client: formData.subadmin,
    };

    if (licensecond === 'Live') {
      delete payload.start_date_client;
      delete payload.end_date_client;
    } else {
      delete payload.to_month;
      delete payload.start_date_client;
      delete payload.end_date_client;
    }
    try {
      console.log(payload, "------------------------------------>>>>")
      console.log(formData, "!!!!!!!!!!!!!!!!!!!!")
      const response = await updateClient(id, payload);
      if (response) {
        toast.success('Client updated successfully!');
        // fetchStrategies();
        navigate('/client/all-clients-list');
      } else {
        toast.error('Failed to update client. Please try again.');
      }
    } catch (error) {
      toast.error('An error occurred while updating the client.');
    } finally {
      setLoading(false);
    }
  };

  const handleCheckboxChange = (strategy) => {
    if (!strategy) {
      console.error('Strategy is undefined');
      return; // Exit the function if strategy is undefined
    }

    // Check if the strategy is already selected
    if (selectedStrategies.includes(strategy.id)) {
      // Remove it if already selected
      setSelectedStrategies(selectedStrategies.filter(id => id !== strategy.id));
    } else {
      // Add it to the selected strategies
      setSelectedStrategies([...selectedStrategies, strategy.id]);
    }
  };

  const handleCheckboxChangesegment = (subsegment) => {
    if (!subsegment) {
      console.error('subsegment is undefined');
      return;
    }

    // Check if the subsegment is already selected
    if (selectedSubsegment.includes(subsegment.id)) {
      // Remove it if already selected
      const updatedSubsegments = selectedSubsegment.filter(id => id !== subsegment.id);
      setSelectedSubsegment(updatedSubsegments);
      setFormData(prevData => ({
        ...prevData,
        subsegment: updatedSubsegments,
      }));
    } else {
      // Add it to the selected subsegment
      const updatedSubsegments = [...selectedSubsegment, subsegment.id];
      setSelectedSubsegment(updatedSubsegments);
      setFormData(prevData => ({
        ...prevData,
        subsegment: updatedSubsegments,
      }));
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
            <h5>Edit Client</h5>
          </CardHeader>
          <CardBody>
            <Form className="needs-validation" noValidate onSubmit={handleSubmit}>
              <Row>
                {/* Common Fields */}
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
                    required
                  />
                  {errors.userName && <div className="invalid-feedback text-danger">{errors.userName}</div>}
                </Col>

                <Col md="4 mb-3">
                  <Label htmlFor="fullName">Full Name
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="text"
                    className={`form-control ${errors.fullName ? 'is-invalid' : ''} custom-input-style`}
                    name="fullName"
                    id="fullName"
                    placeholder="Enter Last Name"
                    value={formData.fullName}
                    onChange={handleChange}
                    required
                  />
                  {errors.fullName && <div className="invalid-feedback text-danger">{errors.fullName}</div>}
                </Col>

                <Col md="4 mb-3">
                  <Label htmlFor="email">Email
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
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
                  <Label htmlFor="mobile">Mobile
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="text"
                    className={`form-control ${errors.mobile ? 'is-invalid' : ''} custom-input-style`}
                    name="mobile"
                    id="mobile"
                    placeholder="Enter Mobile No."
                    value={formData.mobile}
                    onChange={handleChange}
                    required
                  />
                  {errors.mobile && <div className="invalid-feedback text-danger">{errors.mobile}</div>}
                </Col>

                {/* License Field */}
                <Col md="4 mb-3">
                  <Label htmlFor="license">License
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="select"
                    className={`form-control ${errors.license ? 'is-invalid' : ''} custom-input-style`}
                    name="license"
                    id="license"
                    value={formData.license}
                    onChange={handleChange}
                    required
                  >
                    <option value="">Select License</option>
                    {availableLicenses.map((license) => (
                      <option key={license.id} value={license.id}>
                        {license.name}
                      </option>
                    ))}
                  </Input>
                  {errors.license && <div className="invalid-feedback text-danger">{errors.license}</div>}
                </Col>

                <Col md="4 mb-3">
                  <Label htmlFor="groupService">Group Service
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="select"
                    name="groupService"
                    id="groupService"
                    className='custom-input-style'
                    value={formData.groupService}
                    onChange={handleChange}
                    required
                  >
                    <option value="">Select Group Service</option>
                    {groupServices.map((service, index) => (
                      <option key={index} value={service.id}>
                        {service.group_name}
                      </option>
                    ))}
                  </Input>
                </Col>

                <Col md="4 mb-3">
                  <Label htmlFor="subadmin">Sub Admin
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="select"
                    className={`form-control ${errors.subadmin ? 'is-invalid' : ''} custom-input-style`}
                    name="subadmin"
                    id="subadmin"
                    value={formData.subadmin}
                    onChange={handleChange}
                    required
                  >
                    <option value="">Select Sub-Admin</option>
                    {subAdmins.map((user) => (
                      <option key={user.id} value={user.id}>
                        {user.firstName} {user.lastName}
                      </option>
                    ))}
                  </Input>
                  {errors.subadmin && <div className="invalid-feedback text-danger">{errors.subadmin}</div>}
                </Col>

                {/* Conditional fields for Live license */}
                {licensecond === 'Live' && (
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
                {licensecond === 'Demo' && (
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

                <Col md="12" className="mt-2">
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

                <Col md="12" className="mt-2">
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

                <Col md="12" className="mt-4 pb-2 pt-1">
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
                    {loading ? <Spinner size="sm" /> : 'Update'}
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

export default EditClient;
