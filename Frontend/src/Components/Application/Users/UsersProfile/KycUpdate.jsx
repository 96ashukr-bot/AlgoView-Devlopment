import React, { useState } from "react";
import { Col, Container, Form, FormGroup, Input, Label, Row } from "reactstrap";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import "./KycUpdate.css";
import { updateKYC } from "../../../../Services/Authentication";

const KycUpdate = () => {
  const [formValues, setFormValues] = useState({
    idFront: null,
    idBack: null,
    idType: "",
    addressProofFront: null,
    addressProofBack: null,
    addressProofType: "",
  });
  const [previewFront, setPreviewFront] = useState(null);
  const [previewBack, setPreviewBack] = useState(null);
  const [previewAddressFront, setPreviewAddressFront] = useState(null);
  const [previewAddressBack, setPreviewAddressBack] = useState(null);
  const [isFormValid, setIsFormValid] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormValues((prevValues) => {
      const updatedValues = { ...prevValues, [name]: value };
      const allFilled = updatedValues.idType && updatedValues.addressProofType;
      setIsFormValid(allFilled);
      return updatedValues;
    });
  };

  const handleFileChange = (e, type) => {
    const file = e.target.files[0];
    if (file) {
      if (type === "front") {
        setFormValues({ ...formValues, idFront: file });
        setPreviewFront(URL.createObjectURL(file));
      } else if (type === "back") {
        setFormValues({ ...formValues, idBack: file });
        setPreviewBack(URL.createObjectURL(file));
      } else if (type === "addressFront") {
        setFormValues({ ...formValues, addressProofFront: file });
        setPreviewAddressFront(URL.createObjectURL(file));
      } else if (type === "addressBack") {
        setFormValues({ ...formValues, addressProofBack: file });
        setPreviewAddressBack(URL.createObjectURL(file));
      }
    }
  };

  const handleRemoveImage = (type) => {
    if (type === "front") {
      setFormValues({ ...formValues, idFront: null });
      setPreviewFront(null);
    } else if (type === "back") {
      setFormValues({ ...formValues, idBack: null });
      setPreviewBack(null);
    } else if (type === "addressFront") {
      setFormValues({ ...formValues, addressProofFront: null });
      setPreviewAddressFront(null);
    } else if (type === "addressBack") {
      setFormValues({ ...formValues, addressProofBack: null });
      setPreviewAddressBack(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formValues.idType || !formValues.addressProofType) {
      toast.error("All fields are required", {
        position: toast.POSITION.TOP_RIGHT,
        autoClose: 3000,
      });
      return;
    }

    try {
      const response = await updateKYC(formValues);
      toast.success("KYC Updated Successfully!", {
        position: toast.POSITION.TOP_RIGHT,
        autoClose: 3000,
      });

      setFormValues({
        idFront: null,
        idBack: null,
        idType: "",
        addressProofFront: null,
        addressProofBack: null,
        addressProofType: "",
      });
      setPreviewFront(null);
      setPreviewBack(null);
      setPreviewAddressFront(null);
      setPreviewAddressBack(null);
      setIsFormValid(false);
    } catch (error) {
      toast.error(error.message, {
        position: toast.POSITION.TOP_RIGHT,
        autoClose: 3000,
      });
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

                        {/* Personal Details Section */}
                        <h4>Address Proof</h4>
                        <p>Please upload your address proof documents.</p>
                        <Row>
                          <Col md={6}>
                            <FormGroup>
                              <Label className="col-form-label m-0 pt-0 gov-id-head">
                                Select Address Proof Type <span className="text-danger">*</span>
                              </Label>
                              <Input
                                type="select"
                                name="idType"
                                className="form-control"
                                value={formValues.idType}
                                onChange={handleInputChange}
                                required
                              >
                                <option value="" disabled>Select Address Proof Type</option>
                                <option value="Aadhar Card">Aadhar Card</option>
                                <option value="PAN Card">PAN Card</option>
                                <option value="Passport">Passport</option>
                                <option value="Voter Id">Voter Id</option>
                                <option value="Driving License">Driving License</option>
                              </Input>
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
                                <Input className="form-control file-input" type="file" name="idFront" onChange={(e) => handleFileChange(e, "front")} required />
                                <p className="drag-text">Drag and drop file</p>
                              </div>
                            </FormGroup>
                            {previewFront && (
                              <div className="image-preview">
                                <img src={previewFront} alt="ID Front Preview" />
                                <button className="remove-image" onClick={() => handleRemoveImage("front")}>✕</button>
                              </div>
                            )}
                          </Col>
                          <Col md={6}>
                            <FormGroup>
                              <Label className="col-form-label m-0 pt-0 govt-upload-head">
                                Upload Address Proof Back <span className="text-danger">*</span>
                              </Label>
                              <div className="file-upload-wrapper">
                                <Input className="form-control file-input" type="file" name="idBack" onChange={(e) => handleFileChange(e, "back")} required />
                                <p className="drag-text">Drag and drop file</p>
                              </div>
                            </FormGroup>
                            {previewBack && (
                              <div className="image-preview">
                                <img src={previewBack} alt="ID Back Preview" />
                                <button className="remove-image" onClick={() => handleRemoveImage("back")}>✕</button>
                              </div>
                            )}
                          </Col>
                        </Row>

                        <hr className="section-divider" />

                        {/* Address Proof Section */}
                        <h4 className="government-id-section">Government ID</h4>
                        <p>Please upload your Government ID documents.</p>

                        <Row>
                          <Col md={6}>
                            <FormGroup>
                              <Label className="col-form-label m-0 pt-0 gov-id-head">
                                Select Government ID<span className="text-danger">*</span>
                              </Label>
                              <Input
                                type="select"
                                name="addressProofType"
                                className="form-control"
                                value={formValues.addressProofType}
                                onChange={handleInputChange}
                                required
                              >
                                <option value="" disabled>Select ID Type</option>
                                <option value="Aadhar Card">Aadhar Card</option>
                                <option value="PAN Card">PAN Card</option>
                                <option value="Passport">Passport</option>
                                <option value="Voter Id">Voter Id</option>
                                <option value="Driving License">Driving License</option>
                              </Input>
                            </FormGroup>
                          </Col>
                        </Row>

                        <Row>
                          <Col md={6}>
                            <FormGroup>
                              <Label className="col-form-label m-0 pt-0 govt-upload-head">
                                Upload ID Front <span className="text-danger">*</span>
                              </Label>
                              <div className="file-upload-wrapper">
                                <Input className="form-control file-input" type="file" name="addressProofFront" onChange={(e) => handleFileChange(e, "addressFront")} required />
                                <p className="drag-text">Drag and drop file</p>
                              </div>
                            </FormGroup>
                            {previewAddressFront && (
                              <div className="image-preview">
                                <img src={previewAddressFront} alt="Address Proof Front Preview" />
                                <button className="remove-image" onClick={() => handleRemoveImage("addressFront")}>✕</button>
                              </div>
                            )}
                          </Col>
                          <Col md={6}>
                            <FormGroup>
                              <Label className="col-form-label m-0 pt-0 govt-upload-head">
                                Upload ID Back <span className="text-danger">*</span>
                              </Label>
                              <div className="file-upload-wrapper">
                                <Input className="form-control file-input" type="file" name="addressProofBack" onChange={(e) => handleFileChange(e, "addressBack")} required />
                                <p className="drag-text">Drag and drop file</p>
                              </div>
                            </FormGroup>
                            {previewAddressBack && (
                              <div className="image-preview">
                                <img src={previewAddressBack} alt="Address Proof Back Preview" />
                                <button className="remove-image" onClick={() => handleRemoveImage("addressBack")}>✕</button>
                              </div>
                            )}
                          </Col>
                        </Row>

                        <FormGroup className="col-form-label m-0 submit-button-group">
                          <button className="btn btn-primary submit-button" type="submit" disabled={!isFormValid}>
                            Submit KYC
                          </button>
                        </FormGroup>
                      </div>
                    </Form>
                    <ToastContainer />
                  </div>
                </div>
              </div>
            </div>
          </Col>
        </Row>
      </Container>
    </section>
  );
};

export default KycUpdate;
