import React, { useState, useEffect } from 'react';
import {
  Col, Card, CardHeader, CardBody, Form, Label, Row, Input, Button, Spinner
} from 'reactstrap';
import { useNavigate } from 'react-router-dom';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import Swal from 'sweetalert2';
import './ServiceManagement.css';
import { getSegmentsList, createStrategy, } from '../../../../Services/Authentication';

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

const AddStrategies = () => {
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
    fetchSegments();
  }, []);

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
      let updatedValue = inputValue;
      if (name === 'segment') updatedValue = parseInt(inputValue);

      setFormData((prevData) => ({
        ...prevData,
        [name]: updatedValue,
        ...(name === 'executionMode' && updatedValue !== 'MULTI_LEG' ? { multiLegTemplate: '' } : {}),
      }));
    }
    setErrors((prevErrors) => ({ ...prevErrors, [name]: '' }));
  };

  const validateForm = () => {
    const newErrors = {};
    if (!formData.strategyName) newErrors.strategyName = 'Strategy Name is required';
    if (!formData.segment) newErrors.segment = 'Segment is required';
    if (!formData.description) newErrors.description = 'Strategy Description is required';
    if (formData.executionMode === 'MULTI_LEG' && !formData.multiLegTemplate) {
      newErrors.multiLegTemplate = 'Strategy Template is required';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

const handleSubmit = async (e) => {
  e.preventDefault();

  if (!validateForm()) {
    Object.values(errors).forEach((error) => toast.error(error));
    return;
  }

  setLoading(true);
  try {
    const formDataPayload = new FormData();

    // Append non-file fields
    formDataPayload.append('name', formData.strategyName);
    formDataPayload.append('description', formData.description);
    formDataPayload.append('segment', formData.segment);
    formDataPayload.append('execution_mode', formData.executionMode);
    if (formData.executionMode === 'MULTI_LEG') {
      formDataPayload.append('multi_leg_template', formData.multiLegTemplate);
    }

    if (formData.strategyLogo) {
      formDataPayload.append('Strategy_Logo', formData.strategyLogo);
    }

    const response = await createStrategy(formDataPayload); // Send FormData to backend
    console.log('Create response:', response);

    await Swal.fire('Success', 'Strategy added successfully!', 'success');

    setTimeout(() => {
      navigate('/service-manage/strategies');
    }, 2000);
  } catch (error) {
    Swal.fire('Error', error.message || 'Failed to add strategy', 'error');
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
            <h5>Add Strategy</h5>
          </CardHeader>
          <CardBody>
            <Form className="needs-validation" noValidate onSubmit={handleSubmit}>
              <Row>
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
                  {errors.strategyName && (
                    <div className="invalid-feedback text-danger">{errors.strategyName}</div>
                  )}
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
                  {errors.multiLegTemplate && (
                    <div className="invalid-feedback text-danger">{errors.multiLegTemplate}</div>
                  )}
                </Col>

                <Col md="6" className="mb-3">
                  <Label htmlFor="segment">Select Segment
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="select"
                    name="segment"
                    id="segment"
                    value={formData.segment || ''}
                    onChange={handleChange}
                    className={`form-control ${errors.segment ? 'is-invalid' : ''} custom-input-style`}
                    required
                  >
                    <option value="">Select Segment</option>
                    {segments.map((seg) => (
                      <option key={seg.id} value={seg.id}>
                        {seg.name}
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
                    onChange={handleChange}
                    className="form-control custom-input-style"
                  />
                  {previewLogo && (
                    <div className="mt-3 position-relative">
                      <img
                        src={previewLogo}
                        alt="Logo Preview"
                        style={{ maxWidth: '200px', borderRadius: '8px' }}
                      />
                    </div>
                  )}
                </Col>

                {/* Strategy Description */}
                <Col md="12" className="mb-3">
                  <Label htmlFor="description">Strategy Description
                    {/* <span style={{ color: 'red', fontSize: '20px' }}>*</span> */}
                  </Label>
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
                  {errors.description && <div className="invalid-feedback text-danger">{errors.description}</div>}
                </Col>

              </Row>

              <Row>
                <Col className="mt-3">
                  <Button type="submit" className='search-btn-clr' disabled={loading}>
                    {loading ? <Spinner size="sm" /> : 'Add Strategy'}
                  </Button>
                  <Button type="button" color="danger" className="ms-2" onClick={handleCancel}>
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

export default AddStrategies;
