import React, { useState, useEffect } from 'react';
import { Col, Card, CardHeader, CardBody, Form, Label, Row, Input, Button, Spinner, FormGroup } from 'reactstrap';
import { useNavigate } from 'react-router-dom';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { getSegmentsList, getSubSegment, getGroupServicesList, fetchSubAdminsList, addClient, getStrategies, getLicence } from '../../../../Services/Authentication';
import './Clients.css'


const AddClient = () => {
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
  const [selectedGroupService, setSelectedGroupService] = useState(null);


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
    if (selectedGroupService) {
      // Get the strategy IDs from the selected group service
      const strategyIds = selectedGroupService.Strategy.map(strategy => strategy.id);
      setSelectedStrategies(strategyIds);
    } else {
      setSelectedStrategies([]); // Clear selected strategies if no group service is selected
    }
  }, [selectedGroupService]);
  
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

      if (name === 'subsegment') {
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

        const test = [];
        if (selectedService && selectedService.json_data) { // Check if selectedService and json_data exist
          Object.entries(subSegments).forEach(([key, value]) => {
            Object.entries(selectedService.json_data).forEach(([key1, value1]) => {
              if (value.name === value1.ServiceName) {
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
      if (response && Array.isArray(response.results)) {
        setLicenses(response.results);
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
      const response = await getStrategies();
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
    const requiredFields = ['userName', 'fullName', 'email', 'phoneNumber', 'groupService', 'subadmin', 'license',];
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const mobileRegex = /^[0-9]{10}$/;

    if (!formData.email) {
      errors.email = 'Email is required';
    } else if (!emailRegex.test(formData.email)) {
      errors.email = 'Format of email is incorrect';
    }

    if (!formData.phoneNumber) {
      errors.phoneNumber = 'Phone Number number is required';
    } else if (!mobileRegex.test(formData.phoneNumber)) {
      errors.phoneNumber = 'Number must be 10 digits only';
    }

    if (isDemoLicense) {
      requiredFields.push('fromDate', 'toDate');
    } else if (isLiveLicense) {
      requiredFields.push('tomonth');
    }

    requiredFields.forEach(field => {
      if (!formData[field]) {
        errors[field] = 'This field is required';
      }
    });

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

    const selectedLicense = licenses.find(license => license.name.toLowerCase() === formData.license.toLowerCase());
    const licenseId = selectedLicense ? selectedLicense.id : null;

    let payload = {
      email: formData.email,
      userName: formData.userName,
      fullName: formData.fullName,
      phoneNumber: formData.phoneNumber,
      Group_service: formData.groupService,
      assigned_client: formData.subadmin,
      // demate_acc_uid: formData.dematuserid,
      license: licenseId,
      client_status: true,
      segment: formData.segment,
      // subsegment: formData.subsegment,
      subsegment: selectedSubsegment,
      // Strategy: selectedStrategies,
      Strategy: selectedStrategies,
    };

    console.log('Payload before sending to API:', payload);

    if (licenseId) {
      const licenseName = selectedLicense.name.toLowerCase();
      if (licenseName === 'live') {
        payload = {
          ...payload,
          to_month: formData.tomonth,
        };
      } else if (licenseName === 'demo') {
        payload = {
          ...payload,
          start_date_client: formData.fromDate,
          end_date_client: formData.toDate,
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

  const isDemoLicense = formData.license === 'Demo';
  console.log("license", formData.license);
  const isLiveLicense = formData.license === 'Live';


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
                    placeholder="Enter Full Name"
                    value={formData.fullName}
                    onChange={handleChange}
                    required
                  />
                  {errors.fullName && <div className="invalid-feedback text-danger">{errors.fullName}</div>}
                </Col>

                <Col md="4" className="mb-3">
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

                <Col md="4" className="mb-3">
                  <Label htmlFor="phoneNumber">Mobile
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="text"
                    className={`form-control ${errors.phoneNumber ? 'is-invalid' : ''} custom-input-style`}
                    name="phoneNumber"
                    id="phoneNumber"
                    placeholder="Enter Mobile No."
                    value={formData.phoneNumber}
                    onChange={handleChange}
                    required
                  />
                  {errors.phoneNumber && <div className="invalid-feedback text-danger">{errors.phoneNumber}</div>}
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

                    {/* Handle License Based on Selected Option */}
                    <option value="">Select License</option>
                    {licenses.map((license, index) => (
                      <option key={index} value={license.name}>
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
                  {errors.groupService && <div className="invalid-feedback text-danger">{errors.groupService}</div>}
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
                        <option value="1">1</option>
                        <option value="2">2 </option>
                        <option value="3">3 </option>
                        <option value="4">4 </option>
                        <option value="5">5 </option>
                        <option value="6">6 </option>
                        <option value="7">7 </option>
                        <option value="8">8 </option>
                        <option value="9">9 </option>
                        <option value="10">10 </option>
                        <option value="11">11 </option>
                        <option value="12">12 </option>
                      </Input>
                      {errors.tomonth && <div className="invalid-feedback text-danger">{errors.tomonth}</div>}
                    </Col>
                  </>
                )}

                {/* Conditional fields for Demo license */}
                {formData.license === 'Demo' && (
                  <>
                    <Col md="4 mb-3">
                      <Label htmlFor="fromDate">From Date
                        <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                      </Label>
                      <Input
                        type="date"
                        className={`form-control ${errors.fromDate ? 'is-invalid' : ''} custom-input-style`}
                        name="fromDate"
                        id="fromDate"
                        value={formData.fromDate}
                        onChange={handleChange}
                        required
                      />
                      {errors.fromDate && <div className="invalid-feedback text-danger">{errors.fromDate}</div>}
                    </Col>

                    <Col md="4 mb-3">
                      <Label htmlFor="toDate">To Date
                        <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                      </Label>
                      <Input
                        type="date"
                        className={`form-control ${errors.toDate ? 'is-invalid' : ''} custom-input-style`}
                        name="toDate"
                        id="toDate"
                        value={formData.toDate}
                        onChange={handleChange}
                        required
                      />
                      {errors.toDate && <div className="invalid-feedback text-danger">{errors.toDate}</div>}
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
                            {service.ServiceName}[O]
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
                  {strategies.map((strategy) => (
                    <label key={strategy.id} style={{ width: '30%', paddingBottom: '20px', display: 'inline-flex' }}>
                      <input
                        type="checkbox"
                        style={{
                          marginLeft: '20px',
                          transform: 'scale(1.3)',
                          transformOrigin: 'center',
                        }}
                        checked={selectedStrategies.includes(strategy.id)}
                        disabled
                        onChange={() => handleCheckboxChange(strategy)}
                      />
                      <span style={{ marginLeft: '5px' }}>{strategy.name}</span>
                    </label>
                  ))}
                </Col>
                {/* )} */}

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