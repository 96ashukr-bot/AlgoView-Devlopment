import React, { useState, useEffect } from 'react';
import {
  Col, Card, CardHeader, CardBody, Form, Label, Row, Input, Button, Spinner
} from 'reactstrap';
import { useNavigate, useParams } from 'react-router-dom';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './ServiceManagement.css';
import { baseUrl } from '../../../../ConfigUrl/config';
import Swal from 'sweetalert2';
import { getStrategyById, getSegmentsList, updateStrategy,} from '../../../../Services/Authentication'; // Import the updateStrategy function
// import './Settings.css'

const EXECUTION_MODE_OPTIONS = [
  { value: 'INDICATOR_BASED', label: 'Indicator Based Strategies' },
  { value: 'MULTI_LEG', label: 'Multi Leg Option Strategies' },
];

const MULTI_LEG_TEMPLATE_OPTIONS = [
  { value: 'SHORT_STRADDLE', label: 'Short Straddle' },
  { value: 'BULL_CALL_SPREAD', label: 'Bull Call Spread' },
  { value: 'BEAR_CALL_SPREAD', label: 'Bear Call Spread' },
  { value: 'BEAR_PUT_SPREAD', label: 'Bear Put Spread' },
  { value: 'LONG_CALL_BUTTERFLY', label: 'Long Call Butterfly' },
  { value: 'SHORT_CALL_BUTTERFLY', label: 'Short Call Butterfly' },
  { value: 'LONG_CALL_CONDOR', label: 'Long Call Condor' },
  { value: 'SHORT_CALL_CONDOR', label: 'Short Call Condor' },
  { value: 'LONG_IRON_CONDOR', label: 'Long Iron Condor' },
  { value: 'SHORT_IRON_BUTTERFLY', label: 'Short Iron Butterfly' },
];

const EditStrategies = () => {
  const { id } = useParams();
  const [formData, setFormData] = useState({
    id: null,
    strategyName: '',
    segment: '',
    strategyLogo: null,
    description: '',
    executionMode: 'INDICATOR_BASED',
    multiLegTemplate: '',
  });

  const [previewLogo, setPreviewLogo] = useState(null);
  const [segments, setSegments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchStrategy();
    fetchSegments();
  }, []);

  const fetchStrategy = async () => {
    try {
      const strategy = await getStrategyById(id);
      console.log('Fetched Strategy:', strategy);
      
      // Set the form data
      setFormData({
        id: strategy.id,
        strategyName: strategy.name,
        segment: strategy.segment.id, 
        strategyLogo: strategy.Strategy_Logo,
        description: strategy.description,
        executionMode: strategy.execution_mode || 'INDICATOR_BASED',
        multiLegTemplate: strategy.multi_leg_template || '',
      });
  
      // Construct full URLs for previews
      const fullLogoUrl = strategy.Strategy_Logo ? `${baseUrl}${strategy.Strategy_Logo}` : null;
  
      // Preview images if they exist
      if (fullLogoUrl) setPreviewLogo(fullLogoUrl);
  
    } catch (error) {
      Swal.fire('Error', 'Failed to load strategy details', 'error');
    }
  };
  

  const fetchSegments = async () => {
    try {
        const data = await getSegmentsList();
        if (Array.isArray(data)) {
            setSegments(data); 
        } else if (data.results) {
            setSegments(data.results);
        } else {
            throw new Error('Unexpected response structure');
        }
    } catch (err) {
        setError(err.message);
    } finally {
        setLoading(false);
    }
};

  const handleChange = (e) => {
    const { name, value: inputValue, files } = e.target;

    if (files && files[0]) {
      const file = files[0];
      setFormData((prevData) => ({
        ...prevData,
        [name]: file,
      }));

      const imageUrl = URL.createObjectURL(file);

      if (name === 'strategyLogo') {
        setPreviewLogo(imageUrl);
      }
    } else {
      setFormData((prevData) => ({
        ...prevData,
        [name]: inputValue,
        ...(name === 'executionMode' && inputValue !== 'MULTI_LEG' ? { multiLegTemplate: '' } : {}),
      }));
    }

    setErrors((prevErrors) => ({ ...prevErrors, [name]: '' }));
  };

  const validateForm = () => {
    const newErrors = {};
    if (!formData.strategyName) newErrors.strategyName = 'Strategy Name is required';
    if (!formData.segment) newErrors.segment = 'Segment is required';
    if (!formData.description) newErrors.description = 'Strategy Description is required';
    if (formData.executionMode === 'MULTI_LEG' && !formData.multiLegTemplate) newErrors.multiLegTemplate = 'Strategy Template is required';
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
      name: formData.strategyName,
      description: formData.description,
      segment: parseInt(formData.segment),
      execution_mode: formData.executionMode,
      multi_leg_template: formData.executionMode === 'MULTI_LEG' ? formData.multiLegTemplate : null,
    };

    if (formData.strategyLogo instanceof File) {
      payload.Strategy_Logo = formData.strategyLogo;
    }
  
    console.log('Payload:', payload);
  
    setLoading(true);
  
    try {
      const response = await updateStrategy(id, payload);
      console.log('Update response:', response);
      await Swal.fire('Success', 'Strategy updated successfully!', 'success');
      navigate('/service-manage/strategies');
    } catch (error) {
      toast.error(error.message || 'Failed to update strategy');
    } finally {
      setLoading(false);
    }
  };
  

  const handleCancel = () => {
    navigate('/service-manage/strategies');
  };

  return (
    <>
      <ToastContainer />
      <Col sm="12">
        <Card className="mt-5">
          <CardHeader>
            <h5>Edit Strategies</h5>
            {/* <span>Fill in the form below to edit the strategy details. Ensure all required fields are filled.</span> */}
          </CardHeader>
          <CardBody>
            <Form className="needs-validation" noValidate onSubmit={handleSubmit}>
              <Row>
                {/* Strategy Name */}
                <Col md="6" className="mb-3">
                  <Label htmlFor="strategyName">Strategy Name
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="text"
                    name="strategyName"
                    id="strategyName"
                    placeholder="Enter Strategy Name"
                    value={formData.strategyName}
                    onChange={handleChange}
                    className={`form-control ${errors.strategyName ? 'is-invalid' : ''} custom-input-style`}
                    required
                  />
                  {errors.strategyName && <div className="invalid-feedback text-danger">{errors.strategyName}</div>}
                </Col>

                <Col md="6" className="mb-3">
                  <Label htmlFor="executionMode">Strategy Type
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="select"
                    name="executionMode"
                    id="executionMode"
                    value={formData.executionMode}
                    onChange={handleChange}
                    className="custom-input-style"
                  >
                    {EXECUTION_MODE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </Input>
                </Col>

                <Col md="6" className="mb-3">
                  <Label htmlFor="multiLegTemplate">Strategy Template
                    {formData.executionMode === 'MULTI_LEG' && (
                      <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                    )}
                  </Label>
                  <Input
                    type="select"
                    name="multiLegTemplate"
                    id="multiLegTemplate"
                    value={formData.multiLegTemplate}
                    onChange={handleChange}
                    disabled={formData.executionMode !== 'MULTI_LEG'}
                    className={`form-control ${errors.multiLegTemplate ? 'is-invalid' : ''} custom-input-style`}
                  >
                    <option value="">Select Strategy Template</option>
                    {MULTI_LEG_TEMPLATE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </Input>
                  {errors.multiLegTemplate && <div className="invalid-feedback text-danger">{errors.multiLegTemplate}</div>}
                </Col>

                {/* Segment */}
                <Col md="6" className="mb-3">
                  <Label htmlFor="segment">Select Segment
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="select"
                    name="segment"
                    id="segment"
                    value={formData.segment}
                    onChange={handleChange}
                    className={`form-control ${errors.segment ? 'is-invalid' : ''} custom-input-style`}
                    required
                  >
                    <option value="">Select Segment</option>
                    {segments.map((segment) => (
                      <option key={segment.id} value={segment.id}>
                        {segment.name}
                      </option>
                    ))}
                  </Input>
                  {errors.segment && (
                    <div className="invalid-feedback text-danger">{errors.segment}</div>
                  )}
                </Col>

                {/* Strategy Logo */}
                <Col md="6" className="mb-3">
                  <Label htmlFor="strategyLogo">Strategy Logo</Label>
                  <Input
                    type="file"
                    name="strategyLogo"
                    id="strategyLogo"
                    accept="image/*"
                    onChange={handleChange}
                    className={`form-control ${errors.strategyLogo ? 'is-invalid' : ''} custom-input-style`}
                  />
                  {previewLogo && (
                    <div className="preview-container" style={{marginTop:'10px'}}>
                      <img src={previewLogo} alt="Preview" className="preview-image" />
                    </div>
                  )}
                  {errors.strategyLogo && (
                    <div className="invalid-feedback text-danger">{errors.strategyLogo}</div>
                  )}
                </Col>

                {/* Description */}
                <Col md="12" className="mb-3">
                  <Label htmlFor="description">Description</Label>
                  <Input
                    type="textarea"
                    name="description"
                    id="description"
                    placeholder="Enter Strategy Description"
                    value={formData.description}
                    onChange={handleChange}
                    className={`form-control ${errors.description ? 'is-invalid' : ''} custom-input-style`}
                    required
                  />
                  {errors.description && (
                    <div className="invalid-feedback text-danger">{errors.description}</div>
                  )}
                </Col>

              </Row>
              <Button className='search-btn-clr' type="submit" disabled={loading}>
                {loading ? <Spinner size="sm" /> : 'Update Strategy'}
              </Button>
              <Button color="danger" onClick={handleCancel} className="ms-2">Cancel</Button>
            </Form>
          </CardBody>
        </Card>
      </Col>
    </>
  );
};

export default EditStrategies;
