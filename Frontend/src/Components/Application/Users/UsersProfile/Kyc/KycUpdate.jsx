import React, { useState, useEffect } from "react";
import { Col, Container, Form, FormGroup, Input, Label, Row, Alert } from "reactstrap";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { baseUrl } from "../../../../../ConfigUrl/config";
import "./KycUpdate.css";
import { updateKYC, getKYC } from "../../../../../Services/Authentication";

const KycUpdate = () => {
  const [formValues, setFormValues] = useState({
    document_file_front: null,
    document_file_back: null,
    id_proof: "",
    address_prof_front: null,
    address_prof_back: null,
    address_proof_id: "",
  });

  const [previewFront, setPreviewFront] = useState(null);
  const [previewBack, setPreviewBack] = useState(null);
  const [previewAddressFront, setPreviewAddressFront] = useState(null);
  const [previewAddressBack, setPreviewAddressBack] = useState(null);
  const [errors, setErrors] = useState({});
  const [isFormValid, setIsFormValid] = useState(false);
  const [userData, setKycData] = useState([]);
  const [status, setStatus] = useState("");

  const getUserKyc = async () => {
    try {
      const data = await getKYC();
      setFormValues({
        document_file_front: null,
        document_file_back: null,
        id_proof: data.id_proof,
        address_prof_front: null,
        address_prof_back: null,
        address_proof_id: data.address_proof_id,
      });
      setPreviewFront(`${baseUrl}${data.document_file_front}`);
      setPreviewBack(`${baseUrl}${data.document_file_back}`);
      setPreviewAddressFront(`${baseUrl}${data.address_prof_front}`);
      setPreviewAddressBack(`${baseUrl}${data.address_prof_back}`);
      setKycData(data);
      setStatus(data.status); 
    } catch (error) {
      console.error("Error fetching user data:", error);
    }
  };

  useEffect(() => {
    getUserKyc();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormValues((prevValues) => ({
      ...prevValues,
      [name]: value,
    }));
    setErrors((prevErrors) => ({ ...prevErrors, [name]: "" }));
  };
  

  const handleFileChange = (e, type) => {
    const file = e.target.files[0];
    if (file) {
      setIsFormValid(true);
      if (type === "front") {
        setFormValues({ ...formValues, document_file_front: file });
        setPreviewFront(URL.createObjectURL(file));
      } else if (type === "back") {
        setFormValues({ ...formValues, document_file_back: file });
        setPreviewBack(URL.createObjectURL(file));
      } else if (type === "addressFront") {
        setFormValues({ ...formValues, address_prof_front: file });
        setPreviewAddressFront(URL.createObjectURL(file));
      } else if (type === "addressBack") {
        setFormValues({ ...formValues, address_prof_back: file });
        setPreviewAddressBack(URL.createObjectURL(file));
      }
    }
  };

  const handleRemoveImage = (type) => {
    setIsFormValid(true);
    if (type === "front") {
      setFormValues({ ...formValues, document_file_front: null });
      setPreviewFront(null);
    } else if (type === "back") {
      setFormValues({ ...formValues, document_file_back: null });
      setPreviewBack(null);
    } else if (type === "addressFront") {
      setFormValues({ ...formValues, address_prof_front: null });
      setPreviewAddressFront(null);
    } else if (type === "addressBack") {
      setFormValues({ ...formValues, address_prof_back: null });
      setPreviewAddressBack(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation check
    const newErrors = {};
    if (!formValues.id_proof) {
      newErrors.id_proof = "Please select a Document Proof Type.";
    }
    if (!formValues.address_proof_id) {
      newErrors.address_proof_id = "Please select an Address Proof Type.";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      const response = await updateKYC(formValues);
      toast.success("KYC Updated Successfully!", { position: toast.POSITION.TOP_RIGHT, autoClose: 3000 });
      getUserKyc();
    } catch (error) {
      toast.error(error.message, { position: toast.POSITION.TOP_RIGHT, autoClose: 3000 });
    }
  };

  const getAlertColor = () => {
    switch (status.toLowerCase()) {
      case "pending":
        return "primary"; 
      case "rejected":
        return "danger"; 
      case "approved":
        return "success"; 
      default:
        return "secondary";
    }
  };

  return (
    <section>
      <Container className="p-0 login-page" fluid={true}>
        <Row className="m-0">
          <Col className="p-0">
            <div className="login-card">
              <div>
                <div className="kyc-card">
                  <div>
                    <Form className="theme-form login-form" onSubmit={handleSubmit} encType="multipart/form-data">
                      <div className="login-main-new">
                        <div className="kyc-main-head">
                          <h2>Update Your KYC</h2>
                        </div>

                        {/* Alert Section */}
                        {status && (
                          <Alert color={getAlertColor()}>
                            {status === "pending" && "KYC is Pending !"}
                            {status === "rejected" && "KYC is Rejected."}
                            {status === "approved" && "KYC is Approved Successfully."}
                          </Alert>
                        )}

                        {/* Personal Details Section */}
                        <h4 style={{marginTop:'20px'}}>Address Proof</h4>
                        <p>Please upload your address proof documents.</p>
                        <Row>
                          <Col md={6}>
                            <FormGroup>
                              <Label className="col-form-label m-0 pt-0 gov-id-head">
                                Select Address Proof Type <span className="text-danger">*</span>
                              </Label>
                              <Input
                                type="select"
                                name="address_proof_id"
                                className={`form-control ${errors.address_proof_id ? 'is-invalid' : ''}`}
                                value={formValues.address_proof_id}
                                onChange={handleInputChange}
                                
                              >
                                <option value="" disabled>Select Address Proof Type</option>
                                <option value="aadhar_card">Aadhar Card</option>
                                <option value="pan_card">PAN Card</option>
                                <option value="passport">Passport</option>
                                <option value="voter_id">Voter Id</option>
                                <option value="driving-license">Driving License</option>
                              </Input>
                              {errors.address_proof_id && <small className="text-danger">{errors.address_proof_id}</small>}
                            </FormGroup>
                          </Col>
                        </Row>

                        <Row>
                          <Col md={6}>
                            <FormGroup>
                              <Label className="col-form-label m-0 pt-0 govt-upload-head">
                                Upload Address Proof Front <span className="text-danger">*</span>
                              </Label>
                              <div className="file-upload-wrapper">
                                <Input
                                  className="form-control file-input"
                                  type="file"
                                  name="document_file_front"
                                  onChange={(e) => handleFileChange(e, "front")}
                                />
                                <p className="drag-text">Drag and drop file</p>
                              </div>
                            </FormGroup>
                            {previewFront && (
                              <div className="image-preview">
                                <img src={previewFront} alt="ID Front Preview" />
                                <button className="remove-image" onClick={() => handleRemoveImage("front")}>
                                  ✕
                                </button>
                              </div>
                            )}
                          </Col>
                          <Col md={6}>
                            <FormGroup>
                              <Label className="col-form-label m-0 pt-0 govt-upload-head">
                                Upload Address Proof Back <span className="text-danger">*</span>
                              </Label>
                              <div className="file-upload-wrapper">
                                <Input
                                  className="form-control file-input"
                                  type="file"
                                  name="document_file_back"
                                  onChange={(e) => handleFileChange(e, "back")}
                                />
                                <p className="drag-text">Drag and drop file</p>
                              </div>
                            </FormGroup>
                            {previewBack && (
                              <div className="image-preview">
                                <img src={previewBack} alt="ID Back Preview" />
                                <button className="remove-image" onClick={() => handleRemoveImage("back")}>
                                  ✕
                                </button>
                              </div>
                            )}
                          </Col>
                        </Row>

                        <h4>Document ID Proof</h4>
                        <p>Please upload your identity proof documents.</p>
                        <Row>
                          <Col md={6}>
                            <FormGroup>
                              <Label className="col-form-label m-0 pt-0 gov-id-head">
                                Select Document Proof Type <span className="text-danger">*</span>
                              </Label>
                              <Input
                                type="select"
                                name="id_proof"
                                className={`form-control ${errors.id_proof ? 'is-invalid' : ''}`}
                                value={formValues.id_proof}
                                onChange={handleInputChange}
                              >
                                <option value="" disabled>Select Document Proof Type</option>
                                <option value="aadhar_card">Aadhar Card</option>
                                <option value="pan_card">PAN Card</option>
                                <option value="passport">Passport</option>
                                <option value="voter_id">Voter Id</option>
                                <option value="driving-license">Driving License</option>
                              </Input>
                              {errors.id_proof && <small className="text-danger">{errors.id_proof}</small>}
                            </FormGroup>
                          </Col>
                        </Row>

                        <Row>
                          <Col md={6}>
                            <FormGroup>
                              <Label className="col-form-label m-0 pt-0 govt-upload-head">
                                Upload ID Proof Front <span className="text-danger">*</span>
                              </Label>
                              <div className="file-upload-wrapper">
                                <Input
                                  className="form-control file-input"
                                  type="file"
                                  name="address_prof_front"
                                  onChange={(e) => handleFileChange(e, "addressFront")}
                                />
                                <p className="drag-text">Drag and drop file</p>
                              </div>
                            </FormGroup>
                            {previewAddressFront && (
                              <div className="image-preview">
                                <img src={previewAddressFront} alt="Address Proof Front Preview" />
                                <button className="remove-image" onClick={() => handleRemoveImage("addressFront")}>
                                  ✕
                                </button>
                              </div>
                            )}
                          </Col>
                          <Col md={6}>
                            <FormGroup>
                              <Label className="col-form-label m-0 pt-0 govt-upload-head">
                                Upload ID Proof Back <span className="text-danger">*</span>
                              </Label>
                              <div className="file-upload-wrapper">
                                <Input
                                  className="form-control file-input"
                                  type="file"
                                  name="address_prof_back"
                                  onChange={(e) => handleFileChange(e, "addressBack")}
                                
                                />
                                <p className="drag-text">Drag and drop file</p>
                              </div>
                            </FormGroup>
                            {previewAddressBack && (
                              <div className="image-preview">
                                <img src={previewAddressBack} alt="Address Proof Back Preview" />
                                <button className="remove-image" onClick={() => handleRemoveImage("addressBack")}>
                                  ✕
                                </button>
                              </div>
                            )}
                          </Col>
                        </Row>

                        <div className="form-group text-center">
                          <button type="submit" className="btn btn-primary" disabled={!isFormValid}>
                            Update KYC
                          </button>
                        </div>
                      </div>
                    </Form>
                  </div>
                </div>
              </div>
            </div>
          </Col>
        </Row>
      </Container>
      <ToastContainer />
    </section>
  );
};

export default KycUpdate;
