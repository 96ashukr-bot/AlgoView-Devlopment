import React, { useState, useEffect } from 'react';
import {
  Col, Card, CardHeader, CardBody, Form, Label, Row, Input, Button, Spinner, FormGroup
} from 'reactstrap';
import { useNavigate, useParams } from 'react-router-dom';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { AiOutlineCloseCircle } from 'react-icons/ai';
import './ServiceManagement.css';
import { baseUrl } from '../../../../ConfigUrl/config';
import Swal from 'sweetalert2';
import { getStrategyById, getSegmentsList, getCategoriesList, updateStrategy,} from '../../../../Services/Authentication'; // Import the updateStrategy function
// import './Settings.css'

const EditStrategies = () => {
  const { id } = useParams();
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
    fetchStrategy();
    fetchSegments();
    fetchCategories();
  }, []);

  const fetchStrategy = async () => {
    try {
      const strategy = await getStrategyById(id);
      console.log('Fetched Strategy:', strategy);
      
      // Set the form data
      setFormData({
        id: strategy.id,
        strategyName: strategy.name,
        Lots: strategy.Lots,
        category: strategy.category.id,
        segment: strategy.segment.id, 
        indicator: strategy.Indicator,
        strategyTester: strategy.Strategy_Tester,
        strategyLogo: strategy.Strategy_Logo,
        description: strategy.description,
        monthly: strategy.monthly_amount,
        quarterly: strategy.quarterly_amount,
        halfYearly: strategy.half_yearly_amount,
        yearly: strategy.yearly_amount
      });
  
      // Construct full URLs for previews
      const fullIndicatorUrl = strategy.Indicator ? `${baseUrl}${strategy.Indicator}` : null;
      const fullTesterUrl = strategy.Strategy_Tester ? `${baseUrl}${strategy.Strategy_Tester}` : null;
      const fullLogoUrl = strategy.Strategy_Logo ? `${baseUrl}${strategy.Strategy_Logo}` : null;
  
      // Preview images if they exist
      if (fullIndicatorUrl) setPreviewIndicator(fullIndicatorUrl);
      if (fullTesterUrl) setPreviewTester(fullTesterUrl);
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
      setFormData((prevData) => ({
        ...prevData,
        [name]: inputValue,
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
      Object.values(errors).forEach((error) => {
        Swal.fire('Validation Error', error, 'error');
      });
      return;
    }
  
    const payload = {
      name: formData.strategyName,
      description: formData.description,
      Lots: formData.Lots.toString(),
      indicator: formData.indicator || {},
      strategyTester: formData.strategyTester || {},
      strategyLogo: formData.strategyLogo || {},
      monthly_amount: formData.monthly,
      quarterly_amount: formData.quarterly,
      half_yearly_amount: formData.halfYearly,
      yearly_amount: formData.yearly,
      category: formData.category, 
      segment: parseInt(formData.segment), 
    };
  
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

                {/* Per Lot Amount */}
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
                  {errors.Lots && <div className="invalid-feedback text-danger">{errors.Lots}</div>}
                </Col>

                {/* Category */}
                <Col md="6" className="mb-3">
                  <Label htmlFor="category">Select Category
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="select"
                    name="category"
                    id="category"
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
                  </Input>
                  {errors.category && (
                    <div className="invalid-feedback text-danger">{errors.category}</div>
                  )}
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

                {/* Indicator */}
                <Col md="6" className="mb-3">
                  <Label htmlFor="indicator">Indicator
                    <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                  </Label>
                  <Input
                    type="file"
                    name="indicator"
                    id="indicator"
                    accept="image/*"
                    onChange={handleChange}
                    className={`form-control ${errors.indicator ? 'is-invalid' : ''} custom-input-style`}
                  />
                  {previewIndicator && (
                    <div className="preview-container" style={{marginTop:'10px'}}>
                      <img src={previewIndicator} alt="Preview" className="preview-image" />
                      <AiOutlineCloseCircle
                        size={24}
                        className="position-absolute top-0 end-0 text-danger cursor-pointer"
                        onClick={() => removeImage('indicator')}
                      />
                    </div>
                  )}
                  {errors.indicator && (
                    <div className="invalid-feedback text-danger">{errors.indicator}</div>
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
                    accept="image/*"
                    onChange={handleChange}
                    className={`form-control ${errors.strategyTester ? 'is-invalid' : ''} custom-input-style`}
                  />
                  {previewTester && (
                    <div className="preview-container" style={{marginTop:'10px'}}>
                      <img src={previewTester} alt="Preview" className="preview-image" />
                      <AiOutlineCloseCircle
                        size={24}
                        className="position-absolute top-0 end-0 text-danger cursor-pointer"
                        onClick={() => removeImage('strategyTester')}
                      />
                    </div>
                  )}
                  {errors.strategyTester && (
                    <div className="invalid-feedback text-danger">{errors.strategyTester}</div>
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
                    accept="image/*"
                    onChange={handleChange}
                    className={`form-control ${errors.strategyLogo ? 'is-invalid' : ''} custom-input-style`}
                  />
                  {previewLogo && (
                    <div className="preview-container" style={{marginTop:'10px'}}>
                      <img src={previewLogo} alt="Preview" className="preview-image" />
                      <AiOutlineCloseCircle
                        size={24}
                        className="position-absolute top-0 end-0 text-danger cursor-pointer"
                        onClick={() => removeImage('strategyLogo')}
                        style={{cursor: 'pointer'}}
                      />
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
