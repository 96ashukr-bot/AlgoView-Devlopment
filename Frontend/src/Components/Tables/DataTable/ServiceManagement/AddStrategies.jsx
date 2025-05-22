import React, { useState, useEffect } from 'react';
import {
  Col, Card, CardHeader, CardBody, Form, Label, Row, Input, Button, Spinner, FormGroup
} from 'reactstrap';
import { useNavigate } from 'react-router-dom';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import Swal from 'sweetalert2';
import { AiOutlineCloseCircle } from 'react-icons/ai';
import './ServiceManagement.css';
import { getSegmentsList, getCategoriesList, createStrategy, } from '../../../../Services/Authentication';

const AddStrategies = () => {
  const [formData, setFormData] = useState({
    id: null,
    strategyName: '',
    Lots: '',
    category: '',
    segment: '',
    indicator: null,
    strategyTester: null,
    strategyLogo: null,
    description: '',
    monthly: '',
    quarterly: '',
    halfYearly: '',
    yearly: ''
  });

  const [previewIndicator, setPreviewIndicator] = useState(null);
  const [previewTester, setPreviewTester] = useState(null);
  const [previewLogo, setPreviewLogo] = useState(null);
  const [segments, setSegments] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchSegments();
    fetchCategories();
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

const fetchCategories = async () => {
    try {
        const data = await getCategoriesList();
        if (Array.isArray(data)) {
            setCategories(data); 
        } else if (data.results) {
            setCategories(data.results);
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

      if (name === 'indicator') {
        setPreviewIndicator(imageUrl);
      } else if (name === 'strategyTester') {
        setPreviewTester(imageUrl);
      } else if (name === 'strategyLogo') {
        setPreviewLogo(imageUrl);
      }
    } else {
      let updatedValue = inputValue;
      if (name === 'segment') updatedValue = parseInt(inputValue);

      setFormData((prevData) => ({
        ...prevData,
        [name]: updatedValue,
      }));
    }
    setErrors((prevErrors) => ({ ...prevErrors, [name]: '' }));
  };

  const removeImage = (field) => {
    setFormData((prevData) => ({
      ...prevData,
      [field]: null,
    }));

    if (field === 'indicator') {
      setPreviewIndicator(null);
    } else if (field === 'strategyTester') {
      setPreviewTester(null);
    } else if (field === 'strategyLogo') {
      setPreviewLogo(null);
    }
  };

  const validateForm = () => {
    const newErrors = {};
    if (!formData.strategyName) newErrors.strategyName = 'Strategy Name is required';
    if (!formData.Lots) newErrors.Lots = 'Per Lot Amount is required';
    if (!formData.category) newErrors.category = 'Category is required';
    if (!formData.segment) newErrors.segment = 'Segment is required';
    if (!formData.description) newErrors.description = 'Strategy Description is required';
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
    formDataPayload.append('Lots', formData.Lots);
    formDataPayload.append('monthly_amount', formData.monthly);
    formDataPayload.append('quarterly_amount', formData.quarterly);
    formDataPayload.append('half_yearly_amount', formData.halfYearly);
    formDataPayload.append('yearly_amount', formData.yearly);
    formDataPayload.append('category', formData.category);
    formDataPayload.append('segment', formData.segment);

    // Append files if they exist
    if (formData.indicator) {
      formDataPayload.append('Indicator', formData.indicator);
    }
    if (formData.strategyTester) {
      formDataPayload.append('Strategy_Tester ', formData.strategyTester);
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
                  <Label htmlFor="Lots">Per Lot Amount
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="number"
                    name="Lots"
                    id="Lots"
                    placeholder="Enter Per Lot Amount"
                    value={formData.Lots}
                    onChange={handleChange}
                    className={`form-control ${errors.Lots ? 'is-invalid' : ''} custom-input-style`}
                    required
                  />
                  {errors.Lots && (
                    <div className="invalid-feedback text-danger">{errors.Lots}</div>
                  )}
                </Col>

                <Col md="6" className="mb-3">
                  <Label htmlFor="category">Select Category
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="select"
                    name="category"
                    id="category"
                    // placeholder="Enter Category"
                    value={formData.category}
                    onChange={handleChange}
                    className={`form-control ${errors.category ? 'is-invalid' : ''} custom-input-style`}
                    required
                  >
                    <option value="">Select Category</option>
                    {categories.map((category) => (
                      <option key={category.id} value={category.id}>
                        {category.name}
                      </option>
                    ))}
                    {errors.category && (
                      <div className="invalid-feedback text-danger">{errors.category}</div>
                    )}
                  </Input>
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
                <Col md="6" className="mb-3">
                  <Label htmlFor="indicator">Indicator
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="file"
                    name="indicator"
                    id="indicator"
                    onChange={handleChange}
                    className="form-control custom-input-style"
                  />
                  {previewIndicator && (
                    <div className="mt-3 position-relative">
                      <img
                        src={previewIndicator}
                        alt="Indicator Preview"
                        style={{ maxWidth: '200px', borderRadius: '8px' }}
                      />
                      <AiOutlineCloseCircle
                        size={24}
                        className="position-absolute top-0 end-0 text-danger cursor-pointer"
                        onClick={() => removeImage('indicator')}
                      />
                    </div>
                  )}
                </Col>

                {/* Strategy Tester */}
                <Col md="6" className="mb-3">
                  <Label htmlFor="strategyTester">Strategy Tester
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="file"
                    name="strategyTester"
                    id="strategyTester"
                    onChange={handleChange}
                    className="form-control custom-input-style"
                  />
                  {previewTester && (
                    <div className="mt-3 position-relative">
                      <img
                        src={previewTester}
                        alt="Tester Preview"
                        style={{ maxWidth: '200px', borderRadius: '8px' }}
                      />
                      <AiOutlineCloseCircle
                        size={24}
                        className="position-absolute top-0 end-0 text-danger cursor-pointer"
                        onClick={() => removeImage('strategyTester')}
                      />
                    </div>
                  )}
                </Col>

                {/* Strategy Logo */}
                <Col md="6" className="mb-3">
                  <Label htmlFor="strategyLogo">Strategy Logo
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
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
                      <AiOutlineCloseCircle
                        size={24}
                        className="position-absolute top-0 end-0 text-danger cursor-pointer"
                        onClick={() => removeImage('strategyLogo')}
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

                {/* Pricing Plans */}
                <Col md="12" className="mb-3">
                  <h6>Pricing Plans</h6>
                  <Row>
                    <Col md="3" className="mb-3">
                      <Label htmlFor="monthly">Monthly
                        <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                      </Label>
                      <Input
                        type="number"
                        name="monthly"
                        id="monthly"
                        className='custom-input-style'
                        placeholder="Monthly Amount"
                        value={formData.monthly}
                        onChange={handleChange}
                      />
                    </Col>
                    <Col md="3" className="mb-3">
                      <Label htmlFor="quarterly">Quarterly
                        <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                      </Label>
                      <Input
                        type="number"
                        name="quarterly"
                        id="quarterly"
                        className='custom-input-style'
                        placeholder="Quarterly Amount"
                        value={formData.quarterly}
                        onChange={handleChange}
                      />
                    </Col>
                    <Col md="3" className="mb-3">
                      <Label htmlFor="halfYearly">Half Yearly
                        <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                      </Label>
                      <Input
                        type="number"
                        name="halfYearly"
                        id="halfYearly"
                        className='custom-input-style'
                        placeholder="Half Yearly Amount"
                        value={formData.halfYearly}
                        onChange={handleChange}
                      />
                    </Col>
                    <Col md="3" className="mb-3">
                      <Label htmlFor="yearly">Yearly
                        <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                      </Label>
                      <Input
                        type="number"
                        name="yearly"
                        id="yearly"
                        className='custom-input-style'
                        placeholder="Yearly Amount"
                        value={formData.yearly}
                        onChange={handleChange}
                      />
                    </Col>
                  </Row>
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
